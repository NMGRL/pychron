#===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from scipy import optimize
from traits.api import HasTraits, List, Any, Property, Float, Event, Str
from traitsui.api import View, Item, VGroup, HGroup, Spring, \
    TableEditor, RangeEditor
from traitsui.table_column import ObjectColumn

#============= standard library imports ========================
import os
import csv
import time
from numpy import polyval, polyfit, array, min, nonzero, poly1d
#============= local library imports  ==========================
from pychron.helpers.fits import convert_fit
from pychron.paths import paths
# import math
# from pychron.graph.graph import Graph
from pychron.spectrometer.spectrometer_device import SpectrometerDevice
# from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS
# from pychron.regression.ols_regressor import PolynomialRegressor

class CalibrationPoint(HasTraits):
    x = Float
    y = Float


def get_float(func):
    def dec(*args, **kw):
        try:
            return float(func(*args, **kw))
        except (TypeError, ValueError):
            pass

    return dec


class Magnet(SpectrometerDevice):

    _mftable = None

    dac = Property(depends_on='_dac')
    mass = Property(depends_on='_mass')

    _dac = Float
    _mass = Float
    dacmin = Float(0.0)
    dacmax = Float(10.0)

    massmin = Property(Float, depends_on='_massmin')
    massmax = Property(Float, depends_on='_massmax')
    _massmin = Float(0.0)
    _massmax = Float(200.0)

    settling_time = 0.5

    calibration_points = List  # Property(depends_on='mftable')
    detector = Any

    dac_changed = Event

    fitfunc=Str('parabolic')

    def update_field_table(self, isotope, dac):
        """

            dac needs to be in axial units
        """

        self.info('update mftable {} {}'.format(isotope, dac))

        isos, xs, ys = self._get_mftable()

        try:
            refindex = min(nonzero(isos == isotope)[0])

            delta = dac - ys[refindex]
            # need to calculate all ys
            # using simple linear offset
            ys += delta

            self.dump(isos, xs, ys)

            self._mftable = isos, xs, ys

        except ValueError:
            import traceback

            e = traceback.format_exc()
            self.debug('Magnet update field table {}'.format(e))

    def mftable_view(self):
        cols = [ObjectColumn(name='x', label='Mass'),
                ObjectColumn(name='y', label='DAC'),
        ]
        teditor = TableEditor(columns=cols, editable=False)
        v = View(HGroup(
            Item('calibration_points', editor=teditor, show_label=False),
            Item('graph', show_label=False, style='custom')
        ),
                 width=700,
                 height=500,
                 resizable=True

        )
        return v

    #===============================================================================
    # ##positioning
    #===============================================================================
    def set_dac(self, v, verbose=False):
        micro = self.microcontroller
        unblank = False
        if abs(self._dac - v) > 0.1:
            if micro:
                micro.ask('BlankBeam True', verbose=verbose)
                unblank = True

        self._dac = v
        if micro:
            self.microcontroller.ask('SetMagnetDAC {}'.format(v), verbose=verbose)
            time.sleep(self.settling_time)
            if unblank:
                micro.ask('BlankBeam False', verbose=verbose)

        self.dac_changed = True

    @get_float
    def read_dac(self):
        if self.microcontroller is None:
            r = 0
        else:
            r = self.microcontroller.ask('GetMagnetDAC')
        return r

    #===============================================================================
    # persistence
    #===============================================================================
    def load(self):
        pass

    def _get_mftable(self):
        if not self._mftable:
            self._mftable = self._load_mftable()

        return self._mftable

    def _load_mftable(self):
        p = os.path.join(paths.spectrometer_dir, 'mftable.csv')
        self.info('loading mftable {}'.format(p))
        if os.path.isfile(p):
            with open(p, 'U') as f:
                reader = csv.reader(f)
                xs = []
                ys = []
                isos = []

                molweights = self.spectrometer.molecular_weights
                for line in reader:
                    try:
                        fit=int(convert_fit(line[0]))
                    except ValueError:
                        pass

                    try:
                        iso = line[0]
                        x, y = molweights[iso], float(line[1])
                        isos.append(iso)
                        xs.append(x)
                        ys.append(y)
                    except KeyError:
                        self.debug('no molecular weight for {}'.format(line[0]))

            if fit is None:
                fit='parabolic'

            return array(isos), array(xs), array(ys), fit
        else:
            self.warning_dialog('No Magnet Field Table. Create {}'.format(p))

    def finish_loading(self):
        d = self.read_dac()
        if d is not None:
            self._dac = d

    def dump(self, isos, xs, ys):
        p = os.path.join(paths.spectrometer_dir, 'mftable.csv')
        with open(p, 'w') as f:
            writer = csv.writer(f)
            for a in zip(isos, ys):
                writer.writerow(a)

            #===============================================================================
            # mapping
            #===============================================================================

    def map_dac_to_mass(self, d):
        _, xs, ys = self._get_mftable()
        args = polyfit(xs, ys, 2)

        args[-1] -= d
        mass = optimize.brentq(poly1d(args), 0, 200)
        #c = c - d
        #m = (-b + (b * b - 4 * a * c) ** 0.5) / (2 * a)

        return mass

    def map_mass_to_dac(self, mass):
        _, xs, ys, fit= self._get_mftable()

        fit=convert_fit(fit)
        if not isinstance(fit, int):
            self.warning('invalid magnet dac fit= {}'.format(fit))
            return 0

        dac = polyval(polyfit(xs, ys, fit), mass)
        self.debug('map mass to dac {} >> {}'.format(mass, dac))

        return dac

    def map_dac_to_isotope(self, dac=None, det=None):
        if dac is None:
            dac = self._dac
        if det is None:
            det = self.detector

        if det:
            dac = self.spectrometer.uncorrect_dac(det, dac)

        m = self.map_dac_to_mass(dac)
        molweights = self.spectrometer.molecular_weights
        return next((k for k, v in molweights.iteritems() if abs(v - m) < 0.001), None)

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_mass(self):
        return self._mass

    def _set_mass(self, m):
    #        print 'set mass', m
        dac = self.map_mass_to_dac(m)
        if self.detector:
            dac = self.spectrometer.correct_dac(self.detector, dac)

        self._mass = m
        self.dac = dac

    def _validate_dac(self, d):
        return self._validate_float(d)

    def _get_dac(self):
        return self._dac

    def _set_dac(self, v):
        if v is not None:
            self.set_dac(v)

    def _validate_float(self, d):
        try:
            return float(d)
        except (ValueError, TypeError):
            return d

    def _validate_massmin(self, d):
        d = self._validate_float(d)
        if isinstance(d, float):
            if d > self.massmax:
                d = str(d)
        return d

    def _get_massmin(self):
        return self._massmin

    def _set_massmin(self, v):
        self._massmin = v

    def _validate_massmax(self, d):
        d = self._validate_float(d)
        if isinstance(d, float):
            if d < self.massmin:
                d = str(d)
        return d

    def _get_massmax(self):
        return self._massmax

    def _set_massmax(self, v):
        self._massmax = v

    #     def _get_calibration_points(self):
    #
    #         if self.mftable is not None:
    #             molweights = MOLECULAR_WEIGHTS
    # #            molweights = self.spectrometer.molecular_weights
    #             xs, ys = self.mftable
    #             return [CalibrationPoint(x=molweights[xi], y=yi) for xi, yi in zip(xs, ys)]
    #===============================================================================
    # views
    #===============================================================================

    def traits_view(self):
        v = View(
            VGroup(
                VGroup(
                    Item('dac', editor=RangeEditor(low_name='dacmin',
                                                   high_name='dacmax',
                                                   format='%0.5f')),

                    Item('mass', editor=RangeEditor(mode='slider', low_name='massmin',
                                                    high_name='massmax',
                                                    format='%0.3f')),
                    HGroup(Spring(springy=False,
                                  width=48),
                           Item('massmin', width=-40), Spring(springy=False,
                                                              width=138),
                           Item('massmax', width=-55),

                           show_labels=False),
                    show_border=True,
                    label='Control'
                ),
                #                     Group(Item('scanner', style='custom', show_label=False),
                #                           label='Scanner',
                #                           show_border=True)
            )
        )

        return v


if __name__ == '__main__':
    from launchers.helpers import build_version

    build_version('_experiment')
    m = Magnet()
    m.load()
    m.configure_traits()
#============= EOF =============================================
# def get_dac_for_mass(self, mass):
#        reg = self.regressor
#        data = [[MOLECULAR_WEIGHTS[i] for i in self.mftable[0]],
#                self.mftable[1]
#                ]
#        if isinstance(mass, str):
#            mass = MOLECULAR_WEIGHTS[mass]
#
#        if data:
#            dac_value = reg.get_value('parabolic', data, mass)
#        else:
#            dac_value = 4
#
#        return dac_value
#
#    def set_axial_mass(self, x, hv_correction=1, dac=None):
#        '''
#            set the axial detector to mass x
#        '''
#        reg = self.regressor
#
#        if dac is None:
#            data = [[MOLECULAR_WEIGHTS[i] for i in self.mftable[0]],
#                    self.mftable[1]
#                    ]
#            dac = reg.get_value('parabolic', data, x) * hv_correction
#
#        #print x, dac_value, hv_correction
#
#        self.set_dac(dac)
    #    def set_graph(self, pts):
    #
    #        g = Graph(container_dict=dict(padding=10))
    #        g.clear()
    #        g.new_plot(xtitle='Mass',
    #                   ytitle='DAC',
    #                   padding=[30, 0, 0, 30],
    #                   zoom=True,
    #                   pan=True
    #                   )
    #        g.set_x_limits(0, 150)
    #        g.set_y_limits(0, 100)
    #        xs = [cp.x for cp in pts]
    #        ys = [cp.y * 10 for cp in pts]
    #
    #        reg = self.regressor
    #        rdict = reg.parabolic(xs, ys, data_range=(0, 150), npts=5000)
    #
    #        g.new_series(x=xs, y=ys, type='scatter')
    #
    #
    #        g.new_series(x=rdict['x'], y=rdict['y'])
    #        self.graph = g
    #    def calculate_dac(self, pos):
    #        #is pos a number
    #        if not isinstance(pos, (float, int)):
    #            #is pos a isokey or a masskey
    #            # eg. Ar40, or 39.962
    #            mass = None
    #            isokeys = {'Ar40':39.962}
    #            try:
    #                mass = isokeys[pos]
    #            except KeyError:
    #                try:
    #                    mass = float(pos)
    #                except:
    #                    self.debug('invalid magnet position {}'.format(pos))
    #
    #            print 'ionpt', mass, pos,
    #            pos = self.map_mass_to_dac(mass)
    #            print pos

    #        return pos