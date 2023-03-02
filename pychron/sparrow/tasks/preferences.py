# ===============================================================================
# Copyright 2019 ross
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
from traits.api import Str, Password
from traitsui.api import View, Item, HGroup, Spring, VGroup, Label

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.database.tasks.connection_preferences import (
    ConnectionPreferencesPane,
    ConnectionMixin,
)
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper

# class SparrowConnectionFavoriteItem(ConnectionFavoriteItem):
#     kind = 'postgres'
#     port = CInt
#     attributes = ('name', 'username', 'host', 'dbname', 'password', 'enabled', 'default', 'port')
#
#     def __init__(self, schema_identifier='', attrs=None):
#         super(ConnectionFavoriteItem, self).__init__()
#         self.schema_identifier = schema_identifier
#
#         if attrs:
#             attrs = attrs.split(',')
#             try:
#                 (self.name,
#                  self.username,
#                  self.host,
#                  self.dbname,
#                  self.password,
#                  enabled,
#                  default,
#                  self.port) = attrs
#                 self.default = to_bool(default)
#                 self.enabled = to_bool(enabled)
#             except ValueError:
#                 pass
from pychron.sparrow.sparrow_client import SparrowClient


class SparrowPreferences(BasePreferencesHelper, ConnectionMixin):
    preferences_path = "pychron.sparrow"
    host = Str
    password = Password
    username = Str

    def _get_connection_dict(self):
        return dict(
            username=self.username,
            host=self.host,
            password=self.password,
        )

    def _test_connection(self, kw):
        s = SparrowClient(bind=False)
        s.trait_set(**kw)
        ret = s.test_api()
        return ret, None


class SparrowPreferencesPane(ConnectionPreferencesPane):
    model_factory = SparrowPreferences
    category = "Sparrow"

    def traits_view(self):
        cgrp = HGroup(
            Spring(width=10, springy=False),
            icon_button_editor(
                "test_connection_button", "database_connect", tooltip="Test connection"
            ),
            Spring(width=10, springy=False),
            Label("Status:"),
            CustomLabel(
                "_connected_label",
                label="Status",
                weight="bold",
                color_name="_connected_color",
            ),
        )

        massspec_grp = VGroup(
            # Item('enabled', label='Use MassSpec'),
            VGroup(
                Item("host", label="ROOT URL"),
                Item("username", label="User"),
                Item("password", label="Password"),
                cgrp,
                enabled_when="enabled",
                show_border=True,
                label="Connection",
            ),
            label="Sparrow API",
            show_border=True,
        )

        return View(massspec_grp)


# ============= EOF =============================================
