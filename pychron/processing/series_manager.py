#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, Str, List, Bool, Float, Property, Instance, Int
from traitsui.api import View, Item, HGroup, Label, EnumEditor, \
    spring, Group, VGroup
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import re
#============= local library imports  ==========================
from pychron.core.helpers.traitsui_shortcuts import listeditor
from pychron.pychron_constants import FIT_TYPES
import os
from pychron.paths import paths
from pychron.viewable import Viewable


class SeriesOptions(HasTraits):
    name = Str
    show = Bool
    fit = Str
    scalar = Float(1)
    nsigma = Int(1)
    key = Property
    _key = Str

    def traits_view(self):
        v = View(HGroup(Label(self.name),
                        spring,
                        Item('show', show_label=False),
                        Item('fit', editor=EnumEditor(values=FIT_TYPES),
                             show_label=False,
                             enabled_when='show'
                        ))
        )
        return v

    def _fit_default(self):
        return FIT_TYPES[0]

    def _set_key(self, k):
        self._key = k

    def _get_key(self):
        if self._key:
            return self._key
        else:
            return self.name


class PeakCenterOption(HasTraits):
    show = Bool(True)
    plot_centers = Bool(False)

    plot_scans = Bool(True)
    overlay = Bool(False)

    def _plot_centers_changed(self):
        if self.plot_centers:
            self.plot_scans = False

    def _plot_scans_changed(self):
        if self.plot_scans:
            self.plot_centers = False

    def traits_view(self):
        v = View(Item('show', label='Display Peak Center'),
                 HGroup(
                     VGroup(HGroup(Label('Plot Centers')),
                            spring,
                            HGroup(Label('Plot Scans'))
                     ),
                     VGroup(
                         HGroup(Item('plot_centers',
                                     tooltip='Display a time series of peak center values',
                                     show_label=False)),
                         HGroup(
                             Item('plot_scans',
                                  tooltip='Plot peak center scans (DAC vs Intensity)',
                                  show_label=False),
                             Item('overlay',
                                  tooltip='Overlay all scans on one graph',
                                  enabled_when='plot_scans')
                         )
                     ),
                     show_border=True,
                     enabled_when='show'
                 )

                 #                 Group(
                 #                       Item('plot_centers',
                 #                            tooltip='Display a time series of peak center values'
                 #                            ),
                 #                       HGroup(Item('plot_scan', tooltip='Plot peak center scans (DAC vs Intensity)'),
                 #                              Item('overlay',
                 #                                   enabled_when='plot_scan',
                 #                                   tooltip='Overlay all scans on one graph')
                 #                              ),
                 #                       show_border=True,
                 #                       enabled_when='show')
        )
        return v


class SeriesManager(Viewable):
    analyses = List
    series = Property
    calculated_values = List(SeriesOptions)
    measured_values = List(SeriesOptions)
    baseline_values = List(SeriesOptions)
    blank_values = List(SeriesOptions)
    background_values = List(SeriesOptions)
    peak_center_option = Instance(PeakCenterOption, ())
    use_single_window = Bool(False)

    #===============================================================================
    # viewable
    #===============================================================================
    def close(self, isok):
        if isok:
            self.dump()
        return True

    def opened(self, ui):
        self.load()

    #===============================================================================
    # handlers
    #===============================================================================
    def _analyses_changed(self):
        if self.analyses:
            keys = None
            for a in self.analyses:
                nkeys = a.isotope_keys
                if keys is None:
                    keys = set(nkeys)
                else:
                    keys = set(nkeys).intersection(keys)

            keys = sorted(keys,
                          key=lambda x: re.sub('\D', '', x),
                          reverse=True
            )

            self.calculated_values = cv = [SeriesOptions(name=ki, key=ki.replace('Ar', 's')) for ki in keys]
            self.measured_values = [SeriesOptions(name=ki) for ki in keys]
            self.baseline_values = [SeriesOptions(name=ki, key='{}bs'.format(ki)) for ki in keys]
            self.blank_values = [SeriesOptions(name=ki, key='{}bl'.format(ki)) for ki in keys]
            self.background_values = [SeriesOptions(name=ki, key='{}bg'.format(ki)) for ki in keys]
            # make ratios
            for n, d in [('Ar40', 'Ar36')]:
                if n in keys and d in keys:
                    cv.append(SeriesOptions(name='{}/{}'.format(n, d)))

            cv.append(SeriesOptions(name='IC', key='Ar40/Ar36', scalar=295.5))

            #===============================================================================
            # persistence
            #===============================================================================

    def dump(self):
        for ai in ['calculated_values', 'measured_values',
                   'baseline_values', 'blank_values', 'background_values',
                   'peak_center_option'
        ]:
            self._dump(ai)

        p = os.path.join(paths.hidden_dir, 'series_manager.traits')
        with open(p, 'w') as fp:
            dd = dict([(ai, getattr(self, ai)) for ai in ['use_single_window']])
            pickle.dump(dd, fp)

    def _dump(self, attr):
        p = os.path.join(paths.hidden_dir, 'series_manager.{}'.format(attr))
        with open(p, 'w') as fp:
            pickle.dump(getattr(self, attr), fp)

    def load(self):
        for ai in ['calculated_values', 'measured_values',
                   'baseline_values', 'blank_values', 'background_values']:
            self._load(ai, self._load_values)

        self._load('peak_center_option', self._load_peak_center)

        p = os.path.join(paths.hidden_dir, 'series_manager.traits')
        if os.path.isfile(p):
            try:
                with open(p, 'r') as fp:
                    dd = pickle.load(fp)
                    self.trait_set(**dd)
            except pickle.PickleError:
                pass

    def _load(self, attr, func):
        p = os.path.join(paths.hidden_dir, 'series_manager.{}'.format(attr))
        if os.path.isfile(p):
            try:
                with open(p, 'r') as fp:
                    pobj = pickle.load(fp)
                    func(pobj, attr)
            except pickle.PickleError:
                pass

    def _load_values(self, pobj, attr):
        for si in pobj:
            obj = next((ni for ni in getattr(self, attr)
                        if ni.key == si.key and ni.name == si.name), None)
            for ai in ['show', 'fit']:
                setattr(obj, ai, getattr(si, ai))

    def _load_peak_center(self, pobj, attr):
        self.peak_center_option = pobj

    #===============================================================================
    # property get/set
    #===============================================================================
    #    def _get_series(self):
    #        return self.calculated_values + self.measured_values + \
    #                self.baseline_values + self.blank_values
    #===============================================================================
    # views
    #===============================================================================
    def traits_view(self):
        v = View(
            Group(
                Group(Item('peak_center_option', show_label=False, style='custom'),
                      label='Peak Centers'),
                Group(listeditor('calculated_values'), label='Calculated'),
                Group(listeditor('measured_values'), label='Measured'),
                Group(listeditor('baseline_values'), label='Baseline'),
                Group(listeditor('blank_values'), label='Blanks'),
                Group(listeditor('background_values'), label='Backgrounds'),
                layout='tabbed'
            ),
            buttons=['OK', 'Cancel'],
            handler=self.handler_klass,
            title='Select Series',
            width=500

        )
        return v

        #============= EOF =============================================
