# ===============================================================================
# Copyright 2018 Jake Ross
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

from traits.api import Bool
from traitsui.api import View, Item
from apptools.preferences.preferences_helper import PreferencesHelper
from envisage.ui.tasks.preferences_pane import PreferencesPane


class DashboardServerPreferences(PreferencesHelper):
    id = 'pychron.dashboard.server.preferences'
    preferences_path = 'pychron.dashboard.server'

    notifier_enabled = Bool


class DashboardServerPreferencesPane(PreferencesPane):
    category = 'Dashboard'
    model_factory = DashboardServerPreferences

    def traits_view(self):
        v = View(Item('notifier_enabled'))

        return v
# ============= EOF =============================================
