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
#===============================================================================

#============= enthought library imports =======================
from pyface.timer.do_later import do_later
from traits.api import Str, Password, Enum, Button, Bool, \
    on_trait_change, Color, String, Event
from traits.has_traits import HasTraits
from traitsui.api import View, Item, Group, VGroup, HGroup, ListStrEditor, spring, Label, Spring
from envisage.ui.tasks.preferences_pane import PreferencesPane
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter

from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, \
    FavoritesPreferencesHelper, FavoritesAdapter



#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel


class ConnectionMixin(HasTraits):
    test_connection = Button

    connected_label = String('Not Tested')
    connected_color = Color('orange')
    adapter_klass = 'pychron.database.core.database_adapter.DatabaseAdapter'

    def _reset_connection_label(self, d):
        def func():
            self.connected_label = 'Not Tested'
            self.connected_color = 'orange'

        if d:
            do_later(func)
        else:
            func()

    def _get_connection_dict(self):
        raise NotImplementedError

    def _get_adapter(self):
        args = self.adapter_klass.split('.')
        mod, klass = '.'.join(args[:-1]), args[-1]
        mod = __import__(mod, fromlist=[klass])
        return getattr(mod, klass)

    def _test_connection_fired(self):
        kw = self._get_connection_dict()
        klass = self._get_adapter()
        db = klass(**kw)
        self.connected_label = ''
        c = db.connect()
        if c:
            self.connected_color = 'green'
            self.connected_label = 'Connected'
        else:
            self.connected_label = 'Not Connected'
            self.connected_color = 'red'


class ConnectionPreferences(FavoritesPreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.database'
    #id = 'pychron.database.preferences_page'

    #fav_name = Str
    # save_username = Str

    db_name = Str
    username = Str
    password = Password
    host = Str
    kind = Enum('---', 'mysql', 'sqlite')

    def _get_connection_dict(self):
        return dict(username=self.username,
                    host=self.host,
                    password=self.password,
                    name=self.db_name,
                    kind=self.kind)

    def _selected_change_hook(self):
        self._reset_connection_label(True)

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
                             Spring(width=10, springy=False),
                             Label('Status:'),
                             CustomLabel('connected_label',
                                         label='Status',
                                         weight='bold',
                                         color_name='connected_color'),
                             spring,
                             show_labels=False))

        db_grp = Group(HGroup(Item('kind', show_label=False),
                              Item('db_name', label='Name')),
                       # Item('save_username', label='User'),
                       HGroup(fav_grp, db_auth_grp),
                       label='Pychron DB')

        return View(db_grp)


class MassSpecConnectionPreferences(BasePreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.massspec.database'
    name = Str
    username = Str
    password = Password
    host = Str
    adapter_klass = 'pychron.database.adapters.massspec_database_adapter.MassSpecDatabaseAdapter'

    def _anytrait_changed(self, name, old, new):
        if name not in ('connected_label', 'connected_color',
                        'connected_color_',
                        'test_connection'):
            self._reset_connection_label(False)

    def _get_connection_dict(self):
        return dict(username=self.username,
                    host=self.host,
                    password=self.password,
                    name=self.name,
                    kind='mysql')


class MassSpecConnectionPane(PreferencesPane):
    model_factory = MassSpecConnectionPreferences
    category = 'Database'

    def traits_view(self):
        cgrp = HGroup(icon_button_editor('test_connection', 'database_connect',
                                         tooltip='Test connection'),
                      Spring(width=10, springy=False),
                      Label('Status:'),
                      CustomLabel('connected_label',
                                  label='Status',
                                  weight='bold',
                                  color_name='connected_color'))
        massspec_grp = Group(
            VGroup(
                cgrp,
                Item('name', label='Database'),
                Item('host', label='Host'),
                Item('username', label='Name'),
                Item('password', label='Password'),
                show_border=True,
                label='Authentication'),
            label='MassSpec DB')

        return View(massspec_grp)

        #============= EOF =============================================
