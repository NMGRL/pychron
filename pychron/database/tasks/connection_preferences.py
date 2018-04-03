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
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.message_dialog import warning
from pyface.timer.do_later import do_later, do_after
from traits.api import Str, Password, Enum, Button, on_trait_change, Color, String, List, Event, File, HasTraits, Bool
from traitsui.api import View, Item, Group, VGroup, HGroup, ListStrEditor, spring, Label, Spring, \
    EnumEditor, ObjectColumn, TableEditor, UItem
from traitsui.editors import TextEditor, FileEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn

from pychron.core.helpers.strtools import to_bool
from pychron.core.pychron_traits import IPAddress, IPREGEX
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
    except BaseException as e:
        print('exception show names', e)
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


class ConnectionFavoriteItem(HasTraits):
    enabled = Bool
    name = Str
    dbname = Str
    host = Str
    kind = Enum('mysql', 'sqlite')
    username = Str
    names = List
    password = Password
    schema_identifier = Str
    path = File
    default = Bool

    def __init__(self, schema_identifier='', attrs=None):
        super(ConnectionFavoriteItem, self).__init__()
        self.schema_identifier = schema_identifier

        if attrs:
            attrs = attrs.split(',')
            try:
                self.name, self.kind, self.username, self.host, self.dbname, self.password = attrs
            except ValueError:
                try:
                    self.name, self.kind, self.username, self.host, self.dbname, self.password, enabled = attrs
                    self.enabled = to_bool(enabled)
                except ValueError:
                    try:
                        (self.name, self.kind, self.username, self.host, self.dbname,
                         self.password, enabled, default) = attrs

                        self.enabled = to_bool(enabled)
                        self.default = to_bool(default)
                    except ValueError:
                        (self.name, self.kind, self.username, self.host, self.dbname,
                         self.password, enabled, default, path) = attrs
                        self.enabled = to_bool(enabled)
                        self.default = to_bool(default)
                        self.path = path

            self.load_names()

    def load_names(self):
        if self.username and self.host and self.password:
            if self.schema_identifier:
                if IPREGEX.match(self.host) or self.host == 'localhost':
                    names = show_databases(self.host, self.username, self.password, self.schema_identifier)
                    self.names = names

    def to_string(self):
        return ','.join([str(getattr(self, attr)) for attr in ('name', 'kind', 'username', 'host',
                                                               'dbname', 'password', 'enabled', 'default', 'path')])

    def __repr__(self):
        return self.name


class ConnectionPreferences(FavoritesPreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.database'
    add_favorite_path = Button

    _fav_klass = ConnectionFavoriteItem
    _schema_identifier = None

    def __init__(self, *args, **kw):
        super(ConnectionPreferences, self).__init__(*args, **kw)

    def _add_favorite_path_fired(self):
        dlg = FileDialog(action='open')
        if dlg.open() == OK:
            if dlg.path:
                self._fav_items.append(self._fav_factory(kind='sqlite', path=dlg.path, enabled=True))
                self._set_favorites()

    def _fav_factory(self, fav=None, **kw):
        f = self._fav_klass(self._schema_identifier, fav)
        f.trait_set(**kw)

        return f

    def _get_connection_dict(self):

        obj = self._selected

        return dict(username=obj.username,
                    host=obj.host,
                    password=obj.password,
                    name=obj.dbname,
                    kind=obj.kind)

    def __selected_changed(self):
        self._reset_connection_label(True)

    @on_trait_change('_fav_items:+')
    def fav_item_changed(self, obj, name, old, new):
        if name in ('username', 'host', 'password'):
            obj.load_names()
        elif name == 'default':
            if not old:
                if obj.enabled:
                    for fav in self._fav_items:
                        if fav != obj:
                            fav.trait_setq(default=False)
                else:
                    obj.trait_setq(default=False)
            else:
                obj.trait_setq(default=True)

        self._set_favorites()


class ConnectionPreferencesPane(PreferencesPane):
    model_factory = ConnectionPreferences
    category = 'Database'

    def traits_view(self):
        # db_auth_grp = Group(
        #     Item('host',
        #          editor=TextEditor(enter_set=True, auto_set=False),
        #          width=125, label='Host'),
        #     Item('username', label='User',
        #          editor=TextEditor(enter_set=True, auto_set=False)),
        #     Item('password', label='Password',
        #          editor=TextEditor(enter_set=True, auto_set=False, password=True)),
        #     enabled_when='kind=="mysql"',
        #     show_border=True,
        #     label='Authentication')

        cols = [CheckboxColumn(name='enabled'),
                CheckboxColumn(name='default'),
                ObjectColumn(name='kind'),
                ObjectColumn(name='name'),
                ObjectColumn(name='username'),
                ObjectColumn(name='password',
                             format_func=lambda x: '*' * len(x),
                             editor=TextEditor(password=True)),
                ObjectColumn(name='host'),
                ObjectColumn(name='dbname',
                             label='Database',
                             editor=EnumEditor(name='names')),
                ObjectColumn(name='path', style='readonly')]

        fav_grp = VGroup(UItem('_fav_items',
                               width=100,
                               editor=TableEditor(columns=cols,
                                                  selected='_selected',
                                                  sortable=False)),
                         HGroup(
                             icon_button_editor('add_favorite', 'database_add',
                                                tooltip='Add saved connection'),
                             icon_button_editor('add_favorite_path', 'dbs_sqlite',
                                                tooltip='Add sqlite database'),
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

        # db_grp = Group(HGroup(Item('kind', show_label=False),
        #                       Item('name',
        #                            label='Database Name',
        #                            editor=EnumEditor(name='_names'),
        #                            visible_when='kind=="mysql"')),
        #                HGroup(fav_grp, db_auth_grp, visible_when='kind=="mysql"'),
        #
        #                VGroup(Item('path', label='Database File'),
        #                       visible_when='kind=="sqlite"'),
        #                show_border=True,
        #                label='Pychron DB')

        db_grp = HGroup(fav_grp)
        return View(db_grp)

# ============= EOF =============================================
