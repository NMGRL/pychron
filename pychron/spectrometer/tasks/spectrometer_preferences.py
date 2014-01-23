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
from traits.api import Bool, HasTraits, Float, String
from traitsui.api import View, Item, VGroup, HGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


#============= standard library imports ========================
#============= local library imports  ==========================

class ICFactor(HasTraits):
    detector = String
    value = Float
    error = Float


class SpectrometerPreferences(BasePreferencesHelper):
    name = 'Spectrometer'
    preferences_path = 'pychron.spectrometer'
    id = 'pychron.spectrometer.preferences_page'
    send_config_on_startup = Bool

    # stored_ic_factors = List
    #
    # ic_factors = List
    #
    # def _ic_factory(self, detector, **kw):
    #     ic=next((i for i in self.ic_factors if i.detector==detector), None)
    #     if ic is None:
    #         ic = ICFactor(**kw)
    #         ic.on_trait_change(self._ic_update, 'detector,value,error')
    #     return ic
    #
    # def _preferences_changed_listener(self, node, key, old, new):
    #     """ Listener called when a preference value is changed. """
    #
    #     if key == 'ic_factors':
    #         if self.ic_factors:
    #             for ic in self.ic_factors:
    #                 ic.on_trait_change(self._ic_update, 'detector,value,error', remove=True)
    #
    #         new = node._preferences.get('stored_ic_factors')
    #         if new:
    #             ss = []
    #             for si in eval(new):
    #                 d, v, e = si.split(',')
    #                 ic = self._ic_factory(detector=d,
    #                                       value=float(v),
    #                                       error=float(e))
    #                 ss.append(ic)
    #
    #             self.trait_set(ic_factors=ss, trait_change_notify=False)
    #
    #     else:
    #         if key in self.trait_names():
    #             setattr(self, key, self._get_value(key, new))
    #
    # def _initialize(self, preferences, notify=False):
    #     """ Initialize the object's traits from the preferences node. """
    #
    #     path = self._get_path()
    #     keys = preferences.keys(path)
    #
    #     traits_to_set = {}
    #     for trait_name in self.trait_names():
    #         if trait_name == 'ic_factors':
    #             s = preferences.get('{}.{}'.format(path, 'stored_ic_factors'))
    #
    #             if not s:
    #                 self.stored_ic_factors = [',0,0' for i in range(10)]
    #                 self.ic_factors = [self._ic_factory() for i in range(10)]
    #             else:
    #                 ss = []
    #                 ns = eval(s)
    #                 for si in ns:
    #                     d, v, e = si.split(',')
    #                     ic = self._ic_factory(detector=d,
    #                                           value=float(v),
    #                                           error=float(e))
    #                     ss.append(ic)
    #
    #                 self.stored_ic_factors = ns
    #                 self.ic_factors = ss
    #
    #             continue
    #
    #         if trait_name in keys:
    #             key = '%s.%s' % (path, trait_name)
    #             value = self._get_value(trait_name, preferences.get(key))
    #             #print trait_name, key, value
    #             traits_to_set[trait_name] = value
    #
    #     self.set(trait_change_notify=notify, **traits_to_set)
    #
    #     # Listen for changes to the node's preferences.
    #     preferences.add_preferences_listener(
    #         self._preferences_changed_listener, path)
    #
    #     return
    #
    # def _ic_update(self, v):
    #     ics = ['{},{},{}'.format(ic.detector, ic.value, ic.error)
    #            for ic in self.ic_factors]
    #     self.stored_ic_factors = ics


class SpectrometerPreferencesPane(PreferencesPane):
    model_factory = SpectrometerPreferences
    category = 'Spectrometer'

    def traits_view(self):
        # cols = [ObjectColumn(name='detector', label='Detector'),
        #         ObjectColumn(name='value', label='Value', width=100),
        #         ObjectColumn(name='error', label=u'\u00b11\u03c3', width=100)]

        return View(
            VGroup(
                HGroup(
                    Item('send_config_on_startup',
                         tooltip='Load the spectrometer parameters on startup'
                    )),
                # VGroup(
                #     UItem('ic_factors',
                #           editor=TableEditor(columns=cols,
                #                              sortable=False,
                #           ),
                #
                #     ),
                #     label='IC Factors'
                # )
            ),
        )

#============= EOF =============================================
