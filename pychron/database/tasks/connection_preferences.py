#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Password, Enum, Button, on_trait_change, Color
from traitsui.api import View, Item, Group, VGroup, HGroup, ListStrEditor, spring, Label
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, \
    FavoritesPreferencesHelper, FavoritesAdapter



#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.core.ui.custom_label_editor import CustomLabel


class ConnectionPreferences(FavoritesPreferencesHelper):
    preferences_path = 'pychron.database'
    #id = 'pychron.database.preferences_page'

    #fav_name = Str
    save_username = Str
    db_name = Str
    username = Str
    password = Password
    host = Str
    kind = Enum('---', 'mysql', 'sqlite')
    test_connection = Button

    connected_label = Str
    connected_color = Color('green')

    def _selected_change_hook(self):
        self.connected_label = 'Not Tested'
        self.connected_color = 'red'

    def _test_connection_fired(self):
        db = DatabaseAdapter(username=self.username,
                             host=self.host,
                             password=self.password,
                             name=self.db_name,
                             kind=self.kind)

        self.connected_label = ''
        c = db.connect()
        if c:
            self.connected_label = 'Connected'
            self.connected_color = 'green'
        else:
            self.connected_label = 'Not Connected'
            self.connected_color = 'red'

    @on_trait_change('db_name, kind, username, host, password')
    def db_attribute_changed(self, obj, name, old, new):

        if self.favorites:
            idx = ['', 'kind',
                   'username',
                   'host',
                   'db_name',
                   'password']

            for i, fastr in enumerate(self.favorites):
                vs = fastr.split(',')
                if vs[0] == self.fav_name:
                    aind = idx.index(name)
                    fa = fastr.split(',')
                    fa[aind] = new
                    fastr = ','.join(fa)
                    self.favorites[i] = fastr
                    self.selected = fastr
                    break

    def _get_attrs(self):
        return ['fav_name', 'kind', 'username',
                'host', 'db_name', 'password']

    def _get_values(self):
        return [self.fav_name,
                self.kind,
                self.username, self.host,
                self.db_name,
                self.password]


class ConnectionPreferencesPane(PreferencesPane):
    model_factory = ConnectionPreferences
    category = 'Database'

    def traits_view(self):
        db_auth_grp = Group(
            Item('host', width=125, label='Host'),
            Item('username', label='User'),
            Item('password', label='Password'),
            enabled_when='kind=="mysql"',
            show_border=True,
            label='Authentication')

        fav_grp = VGroup(Item('fav_name',
                              show_label=False),
                         Item('favorites',
                              show_label=False,
                              width=100,
                              editor=ListStrEditor(
                                  editable=False,
                                  adapter=FavoritesAdapter(),
                                  selected='object.selected')),
                         HGroup(
                             icon_button_editor('add_favorite', 'add',
                                                tooltip='Add saved connection'),
                             icon_button_editor('delete_favorite', 'delete',
                                                tooltip='Delete saved connection'),
                             icon_button_editor('test_connection', 'database_connect',
                                                tooltip='Test connection'),
                             Label('Status:'),
                             CustomLabel('connected_label',
                                         label='Status',
                                         weight='bold',
                                         color_name='connected_color'),
                             spring,
                             show_labels=False))

        db_grp = Group(HGroup(Item('kind', show_label=False),
                              Item('db_name', label='Name')),
                       Item('save_username', label='User'),
                       HGroup(fav_grp, db_auth_grp),
                       label='Main DB')

        return View(db_grp)


class MassSpecConnectionPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.massspec.database'
    name = Str
    username = Str
    password = Password
    host = Str


class MassSpecConnectionPane(PreferencesPane):
    model_factory = MassSpecConnectionPreferences
    category = 'Database'

    def traits_view(self):
        massspec_grp = Group(
            Group(
                Item('name', label='Database'),
                Item('host', label='Host'),
                Item('username', label='Name'),
                Item('password', label='Password'),
                show_border=True,
                label='Authentication'),
            label='MassSpec DB')

        return View(massspec_grp)

    #============= EOF =============================================
