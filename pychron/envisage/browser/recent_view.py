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
from traits.api import HasTraits, Str, List, Float, Enum
from traitsui.api import View, Item, EnumEditor, CheckListEditor

from pychron.persistence_loggable import PersistenceMixin
from pychron.pychron_constants import ANALYSIS_TYPES

PREFIX = {'Last Day': 24, 'Last Week': 24 * 7, 'Last Month': 24 * 30}


class RecentView(HasTraits, PersistenceMixin):
    mass_spectrometer = Str(dump=True)
    mass_spectrometers = List

    nhours = Float(dump=True)
    ndays = Float(dump=True)

    presets = Enum('Last Day', 'Last Week', 'Last Month', dump=True)
    persistence_path = 'recent_view'

    analysis_types = List(ANALYSIS_TYPES, dump=True)
    available_analysis_types = List(ANALYSIS_TYPES)

    def traits_view(self):
        v = View(Item('presets', label='Presets'),
                 Item('ndays', label='Days'),
                 Item('nhours', label='Hours'),
                 Item('mass_spectrometer', label='Mass Spectrometer',
                      editor=EnumEditor(name='mass_spectrometers')),
                 Item('analysis_types', style='custom',
                      editor=CheckListEditor(name='available_analysis_types', cols=5)),
                 title='Recent Analyses',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v

    def _presets_changed(self, new):
        if new:
            self.nhours = PREFIX[new]

    def _ndays_changed(self, new):
        if new:
            self.nhours = new * 24

# ============= EOF =============================================
