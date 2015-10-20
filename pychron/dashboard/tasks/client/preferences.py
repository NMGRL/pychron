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
from traits.api import HasTraits, Button, Bool, Str, Int
from traitsui.api import View, Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class ExperimentDashboardClientPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dashboard.client'
    use_dashboard_client = Bool


class ExperimentDashboardClientPreferencesPane(PreferencesPane):
    model_factory = ExperimentDashboardClientPreferences
    category = 'Experiment'

    def traits_view(self):
        v = View(Item('use_dashboard_client'))
        return v


class DashboardClientPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dashboard.client'
    host = Str
    port = Int


class DashboardClientPreferencesPane(PreferencesPane):
    model_factory = DashboardClientPreferences
    category = 'Dashboard'

    def traits_view(self):
        v = View(VGroup(Item('host'),
                        Item('port'),
                        show_border=True,
                        label='Dashboard Server'))
        return v
# ============= EOF =============================================



