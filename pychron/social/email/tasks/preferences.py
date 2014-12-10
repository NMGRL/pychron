# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Str, Password, Int, Button, on_trait_change, Color
from traitsui.api import View, Item, Group, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.database.tasks.connection_preferences import ConnectionMixin
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class EmailPreferences(BasePreferencesHelper):
    server_username = Str
    server_password = Password

    server_host = Str
    server_port = Int

    preferences_path = 'pychron.email'
    test_connection_button = Button
    status = Str('Not Tested')
    status_color = Color('orange')

    @on_trait_change('server+')
    def _server_trait_changed(self):
        self.status = 'Not Tested'
        self.status_color = 'orange'

    def _test_connection_button_fired(self):
        from pychron.social.email.emailer import Emailer

        em = Emailer()
        if em.connect(warn=False):
            self.status = 'Connected'
            self.status_color = 'green'
        else:
            self.status = 'Failed'
            self.status_color = 'red'


class EmailPreferencesPane(PreferencesPane):
    model_factory = EmailPreferences
    category = 'Social'

    def traits_view(self):
        grp = Group(Item('server_host', label='Host'),
                    Item('server_username', label='User'),
                    Item('server_password', label='Password'),
                    Item('server_port', label='Port'),
                    HGroup(icon_button_editor('test_connection_button', 'server-connect'),
                           CustomLabel('status', color_name='status_color')),
                    show_border=True,
                    label='Email')
        v = View(grp)
        return v

# ============= EOF =============================================
