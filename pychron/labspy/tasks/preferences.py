# ===============================================================================
# Copyright 2014 Jake Ross
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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import HasTraits, Button, Int, Str
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class LabspyPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.labspy'
    host = Str
    port = Int


class LabspyPreferencesPane(PreferencesPane):
    model_factory = LabspyPreferences
    category = 'Labspy'

    def traits_view(self):
        v = View(Item('host'),
                 Item('port'))
        return v

# ============= EOF =============================================



