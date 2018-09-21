# ===============================================================================
# Copyright 2015 Jake Ross
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

from envisage.ui.tasks.preferences_pane import PreferencesPane
# ============= enthought library imports =======================
from traits.api import Directory, Float, Enum
from traitsui.api import View, Item, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.mdd import GEOMETRIES


class MDDPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.mdd'
    executable_root = Directory
    default_temp_offset = Float
    default_geometry = Enum(*GEOMETRIES)


class MDDPreferencesPane(PreferencesPane):
    model_factory = MDDPreferences
    category = 'Pipeline'

    def traits_view(self):
        v = View(VGroup(Item('executable_root', label='Executables Dir.'),
                        Item('default_temp_offset', label='Default Temp. Offset'),
                        Item('default_geometry', label='Default Geometry'),
                        show_border=True, label='MDD'))
        return v


# ============= EOF =============================================
