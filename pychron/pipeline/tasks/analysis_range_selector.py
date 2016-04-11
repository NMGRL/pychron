# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= enthought library imports =======================

from traits.api import Bool, Float, Date, Enum, List
from traitsui.api import View, UItem, Item, HGroup, VGroup
from traitsui.editors.check_list_editor import CheckListEditor
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================

from pychron.paths import paths
from pychron.persistence_loggable import PersistenceLoggable


class AnalysisRangeSelector(PersistenceLoggable):
    n = Float
    use_date_range = Bool
    low_post = Date
    high_post = Date
    time_units = Enum('Hours', 'Days', 'Weeks')

    selected_mass_spectrometers = List
    available_mass_spectrometers = List

    selected_analysis_types = List
    available_analysis_types = List(['Unknown', 'Blank', 'Air', 'Cocktail'])

    pattributes = ('n', 'use_date_range', 'low_post', 'high_post', 'time_units',
                   'selected_mass_spectrometers', 'selected_analysis_types')

    def set_mass_spectrometers(self, ms):
        self.available_mass_spectrometers = ms
        self.selected_mass_spectrometers = [mi for mi in self.selected_mass_spectrometers if mi in ms]

    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, 'analysis_range_selector.p')

    @property
    def nhours(self):
        v = self.n
        if self.time_units == 'Weeks':
            v *= 7 * 24
        elif self.time_units == 'Days':
            v *= 24
        return v

    def traits_view(self):
        msg = VGroup(UItem('selected_mass_spectrometers',
                           style='custom',
                           editor=CheckListEditor(name='available_mass_spectrometers',
                                                  cols=len(self.available_mass_spectrometers))),
                     show_border=True,
                     label='Mass Spectrometers')

        atg = VGroup(UItem('selected_analysis_types',
                           style='custom',
                           editor=CheckListEditor(name='available_analysis_types',
                                                  cols=len(self.available_analysis_types))),
                     show_border=True,
                     label='Analysis Types')

        v = View(VGroup(msg, atg,
                        HGroup(Item('n', enabled_when='not use_date_range'),
                               UItem('time_units', style='custom')),
                        VGroup('use_date_range',
                               HGroup(UItem('low_post'), UItem('high_post'),
                                      enabled_when='use_date_range'),
                               show_border=True)),
                 buttons=['OK', 'Cancel'])
        return v

# ============= EOF =============================================
