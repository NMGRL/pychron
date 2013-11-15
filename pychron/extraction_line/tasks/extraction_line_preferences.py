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
from traits.api import Str, Bool
from traitsui.api import View, Item, VGroup, HGroup, spring
from envisage.ui.tasks.preferences_pane import PreferencesPane

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class ExtractionLinePreferences(BasePreferencesHelper):
    name = 'ExtractionLine'
    preferences_path = 'pychron.extraction_line'
    id = 'pychron.extraction_line.preferences_page'
    check_master_owner = Bool
    use_network = Bool
    inherit_state = Bool
    display_volume = Bool
    volume_key = Str


class ExtractionLinePreferencesPane(PreferencesPane):
    model_factory = ExtractionLinePreferences
    category = 'ExtractionLine'

    def traits_view(self):
        n_grp = VGroup(
            Item('use_network',
                 tooltip='Flood the extraction line with the maximum state color'
            ),
            VGroup(
                Item('inherit_state',
                     tooltip='Should the valves inherit the maximum state color'
                ),
                enabled_when='use_network'
            ),
            VGroup(
                HGroup(
                    Item('display_volume',
                         tooltip='Display the volume for selected section. \
Hover over section and hit the defined volume key (default="v")'
                    ),
                    Item('volume_key',
                         tooltip='Hit this key to display volume',
                         label='Key',
                         width=50,
                         enabled_when='display_volume'
                    ),
                    spring,
                ),
                label='volume',
                enabled_when='use_network'
            ),
            label='Network',
            #show_border=True
        )

        v_grp = VGroup(
            Item('check_master_owner',
                 label='Check Master Ownership',
                 tooltip='Check valve ownership even if this is the master computer'
            ),
            n_grp,
            show_border=True,
            label='Valves'
        )
        return View(v_grp)

#============= EOF =============================================
