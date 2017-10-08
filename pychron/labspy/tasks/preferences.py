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
from traits.api import Int, Str, Password, Bool
from traitsui.api import View, Item, Spring, Label, VGroup, HGroup

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.database.tasks.connection_preferences import ConnectionMixin
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class LabspyPreferences(BasePreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.labspy'
    host = Str
    port = Int
    password = Password
    name = Str
    username = Str

    use_connection_status = Bool
    connection_status_period = Int

    def _get_connection_dict(self):
        return dict(username=self.username,
                    host=self.host,
                    password=self.password,
                    name=self.name,
                    kind='mysql')


class LabspyPreferencesPane(PreferencesPane):
    model_factory = LabspyPreferences
    category = 'Labspy'

    def traits_view(self):
        dbconngrp = VGroup(Item('name'),
                           Item('host'),
                           Item('username'),
                           Item('password'),
                           HGroup(icon_button_editor('test_connection_button', 'database_connect',
                                                     tooltip='Test connection'),
                                  Spring(width=10, springy=False),
                                  Label('Status:'),
                                  CustomLabel('_connected_label',
                                              label='Status',
                                              weight='bold',
                                              color_name='_connected_color')),
                           label='Database Connection',
                           show_border=True)

        csgrp = VGroup(Item('use_connection_status', label='Use Connection Status',
                            tooltip='Enable connection status checking'),
                       Item('connection_status_period',
                            label='Period (s)',
                            tooltip='Check connection status every X seconds',
                            enabled_when='use_connection_status'),
                       label='Connection Status',
                       show_border=True)

        v = View(VGroup(
            dbconngrp,
            csgrp))
        return v


class LabspyExperimentPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.labspy.experiment'
    enabled = Bool


class LabspyExperimentPreferencesPane(PreferencesPane):
    model_factory = LabspyExperimentPreferences
    category = 'Experiment'

    def traits_view(self):
        v = View(VGroup(Item('enabled', label='Use Labspy'),
                        label='Labspy', show_border=True))
        return v

# ============= EOF =============================================
