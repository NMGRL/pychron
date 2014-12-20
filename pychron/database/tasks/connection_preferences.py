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
from pyface.message_dialog import warning
from pyface.timer.do_later import do_later
import re
from traits.api import Str, Password, Enum, Button, Bool, \
    on_trait_change, Color, String, List
from traits.has_traits import HasTraits
from traitsui.api import View, Item, Group, VGroup, HGroup, ListStrEditor, spring, Label, Spring
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traitsui.editors import TextEditor
from pychron.core.pychron_traits import IPAddress
from pychron.core.ui.combobox_editor import ComboboxEditor

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, \
    FavoritesPreferencesHelper, FavoritesAdapter


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel

# IPREGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


def show_databases(host, user, password):
    import pymysql

    names = []
    try:
        conn = pymysql.connect(host=host, port=3306, user=user,
                               connect_timeout=0.25,
                               passwd=password, db='mysql')
        cur = conn.cursor()
        cur.execute("SHOW DATABASES")
        names = [di[0] for di in cur if di[0] not in ('information_schema',
                                                      'performance_schema', 'mysql')]

    except BaseException:
        pass

    return names


class ConnectionMixin(HasTraits):
    test_connection_button = Button
    # _test_connection_button = Button

    _connected_label = String('Not Tested')
    _connected_color = Color('orange')
    _adapter_klass = 'pychron.database.core.database_adapter.DatabaseAdapter'
    _names = List
    # def __init__(self, *args, **kw):
    # super(ConnectionMixin, self).__init__(*args, **kw)
    #
    # self.names = show_databases()
    #


    def _reset_connection_label(self, d):
        def func():
            self._connected_label = 'Not Tested'
            self._connected_color = 'orange'

        if d:
            do_later(func)
        else:
            func()

    def _get_connection_dict(self):
        raise NotImplementedError

    def _get_adapter(self):
        args = self._adapter_klass.split('.')
        mod, klass = '.'.join(args[:-1]), args[-1]
        mod = __import__(mod, fromlist=[klass])
        return getattr(mod, klass)

    def _test_connection_button_fired(self):
        kw = self._get_connection_dict()
        klass = self._get_adapter()
        db = klass(**kw)
        self._connected_label = ''
        c = db.connect(warn=False)
        if c:
            self._connected_color = 'green'
            self._connected_label = 'Connected'
        else:
            self._connected_label = 'Not Connected'
            self._connected_color = 'red'


class ConnectionPreferences(FavoritesPreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.database'

    db_name = Str

    username = Str
    password = Password
    host = IPAddress
    kind = Enum('---', 'mysql', 'sqlite')

    def __init__(self, *args, **kw):
        super(ConnectionPreferences, self).__init__(*args, **kw)
        self._load_names()

    def _load_names(self):
        if self.username and self.password and self.host:
            if self.host:
                self._names = show_databases(self.host, self.username, self.password)
            else:
                warning(None, 'Invalid IP address format. "{}" e.g 129.255.12.255'.format(self.host))

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
        if name in ('username', 'host', 'password'):
            self._load_names()

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
            Item('host',
                 editor=TextEditor(enter_set=True, auto_set=False),
                 width=125, label='Host'),
            Item('username', label='User',
                 editor=TextEditor(enter_set=True, auto_set=False)),
            Item('password', label='Password',
                 editor=TextEditor(enter_set=True, auto_set=False, password=True)),
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
                             icon_button_editor('test_connection_button', 'database_connect',
                                                tooltip='Test connection'),
                             Spring(width=10, springy=False),
                             Label('Status:'),
                             CustomLabel('_connected_label',
                                         label='Status',
                                         weight='bold',
                                         color_name='_connected_color'),
                             spring,
                             show_labels=False))

        db_grp = Group(HGroup(Item('kind', show_label=False),
                              Item('db_name',
                                   label='Database Name',
                                   editor=ComboboxEditor(name='_names'))),
                       # Item('save_username', label='User'),
                       HGroup(fav_grp, db_auth_grp),
                       show_border=True,
                       label='Pychron DB')

        return View(db_grp)


class MassSpecConnectionPreferences(BasePreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.massspec.database'
    name = Str
    username = Str
    password = Password
    host = Str
    _adapter_klass = 'pychron.database.adapters.massspec_database_adapter.MassSpecDatabaseAdapter'
    enabled = Bool

    def _anytrait_changed(self, name, old, new):
        if name not in ('_connected_label', '_connected_color',
                        '_connected_color_',
                        'test_connection'):
            self._reset_connection_label(False)
        super(MassSpecConnectionPreferences, self)._anytrait_changed(name, old, new)

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
        cgrp = HGroup(Spring(width=10, springy=False),
                      icon_button_editor('test_connection_button', 'database_connect',
                                         tooltip='Test connection'),
                      Spring(width=10, springy=False),
                      Label('Status:'),
                      CustomLabel('_connected_label',
                                  label='Status',
                                  weight='bold',
                                  color_name='_connected_color'))

        massspec_grp = VGroup(Item('enabled', label='Use MassSpec'),
                              VGroup(
                                  cgrp,
                                  Item('name', label='Database'),
                                  Item('host', label='Host'),
                                  Item('username', label='Name'),
                                  Item('password', label='Password'),
                                  enabled_when='enabled',
                                  show_border=True,
                                  label='Authentication'),
                              label='MassSpec DB',
                              show_border=True)

        return View(massspec_grp)

# ============= EOF =============================================
