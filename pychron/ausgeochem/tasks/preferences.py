# ===============================================================================
# Copyright 2024 Pychron Developers
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

from __future__ import absolute_import

from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Password, Str
from traitsui.api import Item, View, VGroup

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class AusGeochemPreferences(BasePreferencesHelper):
    preferences_path = "pychron.ausgeochem"
    base_url = Str("https://app.ausgeochem.org")
    username = Str
    password = Password


class AusGeochemPreferencesPane(PreferencesPane):
    model_factory = AusGeochemPreferences
    category = "AusGeochem"

    def traits_view(self):
        auth_grp = VGroup(
            Item("base_url", label="Base URL"),
            Item("username"),
            Item("password"),
            label="EarthData",
            show_border=True,
        )
        return View(auth_grp)


# ============= EOF =============================================
