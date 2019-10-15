# ===============================================================================
# Copyright 2017 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from traits.api import HasTraits, List, Float, Enum, Bool
from traitsui.api import Item, CheckListEditor, UItem, HGroup, VGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderHGroup
from pychron.persistence_loggable import PersistenceMixin
from pychron.pychron_constants import ANALYSIS_TYPES, NULL_STR

PREFIX = {'Last Day': 24, 'Last Week': 24 * 7, 'Last Month': 24 * 30}


class RecentView(HasTraits, PersistenceMixin):
    mass_spectrometers = List(dump=True)
    available_mass_spectrometers = List
    use_mass_spectrometers = Bool

    nhours = Float(dump=True)
    ndays = Float(dump=True)

    presets = Enum(NULL_STR, 'Last Day', 'Last Week', 'Last Month', dump=True)

    analysis_types = List(ANALYSIS_TYPES, dump=True)
    available_analysis_types = List(ANALYSIS_TYPES)

    persistence_name = 'recent_view'

    def traits_view(self):
        v = okcancel_view(VGroup(HGroup(BorderHGroup(UItem('presets', ),
                                                     label='Presets'),
                                        BorderHGroup(Item('ndays', label='Days',
                                                          tooltip='Number of days. Set Presets to --- to enable',
                                                          enabled_when='presets=="---"'),
                                                     UItem('nhours',
                                                           tooltip='Number of hours. Set Presets to --- to enable',
                                                           enabled_when='presets=="---"'),
                                                     label='Time')),
                                 BorderHGroup(UItem('mass_spectrometers',
                                                    style='custom',
                                                    editor=CheckListEditor(name='available_mass_spectrometers',
                                                                           cols=5)),
                                              defined_when='use_mass_spectrometers',
                                              label='Mass Spectrometers'),
                                 BorderHGroup(UItem('analysis_types', style='custom',
                                                    editor=CheckListEditor(name='available_analysis_types', cols=5)),
                                              label='Analysis Types')),
                          title='Recent Analyses')
        return v

    def _presets_changed(self, new):
        if new and new != NULL_STR:
            self.nhours = PREFIX[new]

    def _ndays_changed(self, new):
        if new:
            self.presets = NULL_STR
            self.nhours = new * 24

# ============= EOF =============================================
