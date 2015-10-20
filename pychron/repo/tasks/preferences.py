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

# ============= enthought library imports =======================
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Password
from traitsui.api import View, Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class IGSNPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.igsn'
    url = Str
    username = Str
    password = Password


class IGSNPreferencesPane(PreferencesPane):
    model_factory = IGSNPreferences
    category = 'IGSN'

    def traits_view(self):
        auth_grp = VGroup(Item('username'),
                          Item('password'),
                          show_border=True,
                          label='Authentication')

        v = View(VGroup(Item('url', label='IGSN URL'),
                        auth_grp))
        return v

# ============= EOF =============================================
