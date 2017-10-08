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
from pyface.message_dialog import warning
from pyface.timer.do_later import do_later, do_after
from traits.api import Str, Password, Enum, Button, on_trait_change, Color, String, List, Event, File
from traits.has_traits import HasTraits
from traitsui.api import View, Item, Group, VGroup, HGroup, ListStrEditor, spring, Label, Spring, EnumEditor
from traitsui.editors import TextEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import IPAddress
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import FavoritesPreferencesHelper, FavoritesAdapter
from pychron.core.ui.custom_label_editor import CustomLabel

# IPREGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


def show_databases(host, user, password, schema_identifier='AnalysisTbl', exclude=None):
    import pymysql
    if exclude is None:
        exclude = ('information_schema', 'performance_schema', 'mysql')
    names = []
    try:
        conn = pymysql.connect(host=host, port=3306, user=user,
                               connect_timeout=0.25,
                               passwd=password, db='information_schema')
        cur = conn.cursor()
        if schema_identifier:
            sql = '''select TABLE_SCHEMA from
TABLES
where TABLE_NAME="{}"'''.format(schema_identifier)
        else:
            sql = 'SHOW TABLES'

        cur.execute(sql)

        names = [di[0] for di in cur if di[0] not in exclude]

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
    _test_func = None

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
        if self._test_func:
            db.test_func = self._test_func

        c = db.connect(warn=False)
        if c:
            self._connected_color = 'green'
            self._connected_label = 'Connected'
        else:
            self._connected_label = 'Not Connected'
            self._connected_color = 'red'


class ConnectionPreferences(FavoritesPreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.database'

    name = Str

    username = Str
    password = Password
    host = IPAddress
    kind = Enum('---', 'mysql', 'sqlite')
    path = File

    _progress_icon = Str('process-working-2')
    _progress_state = Event
    _schema_identifier = None

    def __init__(self, *args, **kw):
        super(ConnectionPreferences, self).__init__(*args, **kw)
        self._load_names()

    def _load_names(self):
        if self.username and self.password and self.host:
            if self.host:
                def func():
                    self._progress_state = True
                do_after(50, func)

                self._names = show_databases(self.host, self.username, self.password, self._schema_identifier)

                def func():
                    self._progress_state = True

                do_after(50, func)

            else:
                warning(None, 'Invalid IP address format. "{}" e.g 129.255.12.255'.format(self.host))

    def _get_connection_dict(self):
        return dict(username=self.username,
                    host=self.host,
                    password=self.password,
                    name=self.name,
                    kind=self.kind)

    def _selected_change_hook(self):
        self._reset_connection_label(True)

    @on_trait_change('name, kind, username, host, password')
    def db_attribute_changed(self, obj, name, old, new):
        if name in ('username', 'host', 'password'):
            self._load_names()

        if self.favorites:
            idx = ['', 'kind',
                   'username',
                   'host',
                   'name',
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
                'host', 'name', 'password']

    def _get_values(self):
        return [self.fav_name,
                self.kind,
                self.username, self.host,
                self.name,
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
                              Item('name',
                                   label='Database Name',
                                   editor=EnumEditor(name='_names'),
                                   visible_when='kind=="mysql"')),
                       HGroup(fav_grp, db_auth_grp, visible_when='kind=="mysql"'),
                       VGroup(Item('path', label='Database File'),
                              visible_when='kind=="sqlite"'),
                       show_border=True,
                       label='Pychron DB')

        return View(db_grp)

# ============= EOF =============================================
