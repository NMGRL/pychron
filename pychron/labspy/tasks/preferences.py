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
# ============= standard library imports ========================
# ============= local library imports  ==========================
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
        dbconngrp = HGroup(icon_button_editor('test_connection_button', 'database_connect',
                                              tooltip='Test connection'),
                           Spring(width=10, springy=False),
                           Label('Status:'),
                           CustomLabel('_connected_label',
                                       label='Status',
                                       weight='bold',
                                       color_name='_connected_color'))
        csgrp = VGroup(Item('use_connection_status'),
                       Item('connection_status_period', enabled_when='use_connection_status'))

        v = View(VGroup(Item('name'),
                        Item('host'),
                        Item('username'),
                        Item('password'),
                        dbconngrp,
                        csgrp))
        return v

# ============= EOF =============================================
