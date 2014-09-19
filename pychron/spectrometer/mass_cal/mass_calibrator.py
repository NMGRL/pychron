#===============================================================================
# Copyright 2013 Jake Ross
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

from traits.api import HasTraits, Float, Int, List, Str, Any, Event, Property, on_trait_change, Range
from traitsui.api import View, Item, HGroup, spring, EnumEditor, ButtonEditor, Group, TextEditor

#============= standard library imports ========================
from numpy import array, hstack, Inf, savetxt
import csv
import os
from threading import Thread
import struct
#============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.paths import paths
from pychron.spectrometer.jobs.magnet_scan import MagnetScan
from pychron.core.stats.peak_detection import find_peaks, calculate_peak_center, PeakCenterError
from pychron.core.ui.gui import invoke_in_main_thread

DELTA_TOOLTIP = """The minimum difference between a peak and
the following points, before a peak may be considered a peak"""


class CalibrationPeak(HasTraits):
    isotope = Str('Ar40')
    dac = Float
    isotopes = List
    ruler = Any


class MassCalibratorScan(MagnetScan):
    db = Any

    start_dac = Float(4)
    stop_dac = Float(8.0)
    step_dac = Float(0.1)
    period = 10

    calibration_peaks = List

    selected = Any

    #peak detection tuning parameters
    min_peak_height = Float(1)
    min_peak_separation = Range(0.0001, 1000)
    # if the next point is less than delta from the current point than this is not a peak
    # essentially how much does the peak stand out from the background
    delta = Float(1)

    fperiod = Int(50)
    fwindow = Float(1)
    fstep_dac = Float(0.1)
    fexecute_button = Event
    fexecute_label = Property(depends_on='_alive')
    fine_scan_enabled = Property(depends_on='calibration_peaks:isotope')

    _fine_scanning = False

    def setup_graph(self):
        g = self.graph
        g.new_plot()
        g.set_x_title('DAC')

        g.new_series()

        mi = min(self.start_dac, self.stop_dac)
        ma = max(self.start_dac, self.stop_dac)

        g.set_x_limits(min_=mi, max_=ma, pad='0.1')

    def _fine_scan(self):
        operiod = self.period
        self.period = self.fperiod

        self._fine_scanning = True
        i = 1
        self.graph.new_plot(padding_top=10,
                            xtitle='Relative DAC')
        w = self.fwindow / 2.0
        self.graph.set_x_limits(min_=-w, max_=w, plotid=1)
        self._redraw()

        for cp in self.calibration_peaks:
            if not cp.isotope:
                continue

            if self.isAlive():
                self.selected = cp
                self.info('Fine scan calibration peak {}. {} dac={}'.format(i, cp.isotope, cp.dac))
                self._fine_scan_peak(cp)

            i += 1

        self.period = operiod
        self._fine_scanning = False
        if self.isAlive():
            if self.confirmation_dialog('Save to Database'):
                self._save_to_db()
                if self.confirmation_dialog('Apply Calibration'):
                    self._apply_calibration()

    def _pack(self, d):
        data = ''.join([struct.pack('>ff', x, y)
                        for x, y in d])
        return data

    def _save_to_db(self):
        db = self.db
        with db.session_ctx():
            spectrometer = 'Obama'
            hist = db.add_mass_calibration_history(spectrometer)

            #add coarse scan
            d = self._get_coarse_data()
            data = self._pack(d)
            db.add_mass_calibration_scan(hist, blob=data)

            #add fine scans
            plot = self.graph.plots[1]
            cps = [cp for cp in self.calibration_peaks if cp.isotope]
            for cp, ki in zip(cps, sorted(plot.plots.keys())):
                p = plot.plots[ki][0]

                xs = p.index.get_data()
                ys = p.value.get_data()
                d = array((xs, ys)).T
                data = self._pack(d)
                db.add_mass_calibration_scan(hist,
                                             cp.isotope,
                                             blob=data,
                                             center=cp.dac, )


    def _apply_calibration(self):
        """
            save calibration peaks as mag field table
        """
        p = os.path.join(paths.spectrometer_dir, 'mftable.csv')
        with open(p, 'w') as fp:
            writer = csv.writer(fp, delimiter=',')
            for cp in self.calibration_peaks:
                if cp.isotope:
                    writer.writerow([cp.isotope, cp.dac])

    def _fine_scan_peak(self, cp):
        line, _ = self.graph.new_series(plotid=1)

        c = cp.dac
        w = self.fwindow / 2.0

        steps = self._calc_step_values(c - w, c + w, self.fstep_dac)
        self._scan_dac(steps)

        #get last scan
        xs = line.index.get_data()
        ys = line.value.get_data()

        try:
            center = calculate_peak_center(xs, ys)

        # if not isinstance(center, str):
            [lx, cx, hx], [ly, cy, hy], mx, my = center
            self.graph.add_vertical_rule(cx, plotid=1)
            self.info('new peak center. {} nominal={} dx={}'.format(cp.isotope, cp.dac, cx))
            cp.dac += cx
            self._redraw()
        except PeakCenterError,e:
            self.warning(e)
        # else:
        #     self.warning(center)

    def _update_graph_data(self, *args, **kw):
        """
            add and scale scans
        """
        if self._fine_scanning:
            self._update_fine_graph_data(*args, **kw)
        else:
            super(MassCalibratorScan, self)._update_graph_data(*args, **kw)

    def _update_fine_graph_data(self, plot, di, intensities, **kw):
        #print di, intensities

        #convert dac to a relative dac
        di -= self.selected.dac

        ks = sorted(plot.plots.keys())
        cur = plot.plots[ks[-1]][0]

        if hasattr(cur, 'odata'):
            oys = getattr(cur, 'odata')
            oys = hstack((oys, intensities[:1]))
        else:
            oys = array(intensities)

        setattr(cur, 'odata', oys)

        xs = cur.index.get_data()
        xs = hstack((xs, di))
        cur.index.set_data(xs)

        _R = -Inf
        #get the max range and normalize all series
        for p in plot.plots.itervalues():
            p = p[0]
            high, low = max(p.odata), min(p.odata)
            tR = high - low
            if tR > _R:
                _R = tR
                miR = low

        for p in plot.plots.itervalues():
            p = p[0]
            oys = p.odata
            high, low = max(p.odata), min(p.odata)
            r = high - low
            if r:
                oys = (oys - low) * _R / r + miR

            p.value.set_data(oys)

    def _fine_graph_hook(self, *args, **kw):
        plot = self.graph.plots[1]
        self._update_graph_data(plot, *args, **kw)

    def _graph_hook(self, *args, **kw):
        if self._fine_scanning:
            self._fine_graph_hook(*args, **kw)
        else:
            super(MassCalibratorScan, self)._graph_hook(*args, **kw)

    def _dump_scan(self):
        root = os.path.join(paths.data_dir, 'mass_calibration_scans')
        if not os.path.isdir(root):
            os.mkdir(root)

        p, _ = unique_path(root, 'scan')

        d = self._get_coarse_data()
        savetxt(p, d)

    def _get_coarse_data(self):
        """
            return coarse scan as (dac,intensity) pairs
        """
        data = self.graph.plots[0].data
        xs = data.get_data('x0')
        ys = data.get_data('y0')
        return array((xs, ys)).T

    def _find_peaks(self):
        if self.graph.plots:
            #clear peaks
            self.graph.remove_rulers()

            data = self.graph.plots[0].data
            xs = data.get_data('x0')
            ys = data.get_data('y0')
            if len(xs) and len(ys):
                lookahead = max(1, int(self.min_peak_separation / self.fstep_dac))

                mxp, mip = find_peaks(ys, xs,
                                      lookahead=lookahead,
                                      delta=self.delta)

                pks = []
                isos = self.spectrometer.molecular_weights.keys()
                isos = sort_isotopes(isos)

                for dac, v in mxp:
                    if v > self.min_peak_height:
                        l = self.graph.add_vertical_rule(dac)
                        pks.append(CalibrationPeak(dac=dac,
                                                   isotopes=isos,
                                                   ruler=l))

                self.calibration_peaks = pks
            self._redraw()

    def _set_x_limits(self):

        if self.graph:
            mi = min(self.start_dac, self.stop_dac)
            ma = max(self.start_dac, self.stop_dac)

            self.graph.set_x_limits(min_=mi, max_=ma, pad='0.1')

    def _redraw(self):
        invoke_in_main_thread(self.graph.redraw)

    def _execute(self):
        self.spectrometer.magnet.settling_time = 0.001

        sm = self.start_dac
        em = self.stop_dac
        stm = self.step_dac

        self.verbose = True
        if abs(sm - em) > stm:
            #do initial scan
            self._do_scan(sm, em, stm, map_mass=False)
            self._alive = False

            #write data to file for testing
            self._dump_scan()

            #find peaks
            self._find_peaks()

            self._post_execute()

        self.verbose = False

    def _end(self):
        self._fine_scanning = False

    #===================================================================================================================
    # handlers
    #===================================================================================================================
    @on_trait_change('min_peak_height, min_peak_separation, delta')
    def _handle_peak_detection_change(self):
        self._find_peaks()

    def _fexecute_button_fired(self):
        if self.isAlive():
            self.stop()
            self._end()
        else:
            self._alive = True
            t = Thread(name='fine scan',
                       target=self._fine_scan)
            t.start()

    def _selected_changed(self):
        for p in self.calibration_peaks:
            ruler = p.ruler
            ruler.line_width = 1
            ruler.color = (1.0, 0, 0)

        if self.selected:
            self.selected.ruler.line_width = 5
            self.selected.ruler.color = (0, 1.0, 0)

        self.graph.redraw()

    def _start_dac_changed(self):
        self._set_x_limits()

    def _stop_dac_changed(self):
        self._set_x_limits()

    def traits_view(self):
        coarse_grp = Group(
            Item('reference_detector', editor=EnumEditor(name='detectors')),
            Item('start_dac', label='Start'),
            Item('stop_dac', label='Stop'),
            Item('step_dac', label='Step'),
            Item('period', label='Scan Period (ms)'),
            HGroup(spring, Item('execute_button', editor=ButtonEditor(label_value='execute_label'),
                                show_label=False)),
            label='Coarse')

        peak_detection_grp = Group(
            Item('min_peak_height',
                 label='Min. Height (fA)'),
            Item('min_peak_separation',
                 label='Min. Separation (V)',
                 editor=TextEditor(evaluate=float)),
            Item('delta',
                 tooltip=DELTA_TOOLTIP
            ),
            label='Peak Detection')

        fine_grp = Group(
            Item('fwindow', label='Window (V)',
                 tooltip='+/- volts centered at peak_i'),
            Item('fperiod', label='Scan Period (ms)',
                 tooltip='fine scan integration time'
            ),
            HGroup(spring, Item('fexecute_button',
                                editor=ButtonEditor(label_value='fexecute_label'),
                                show_label=False)),
            label='Fine',
            enabled_when='fine_scan_enabled'
        )
        v = View(Group(coarse_grp, peak_detection_grp, fine_grp, layout='tabbed'))
        return v

    def _get_fine_scan_enabled(self):
        return len([cp for cp in self.calibration_peaks
                    if cp.isotope]) > 2


    def _get_fexecute_label(self):
        return 'Stop' if self.isAlive() else 'Start'

        #============= EOF =============================================

