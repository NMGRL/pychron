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
import os

from envisage.ui.tasks.preferences_pane import PreferencesPane
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.message_dialog import warning, information
from pyface.timer.do_later import do_later
from traits.api import (
    Str,
    Password,
    Enum,
    Button,
    on_trait_change,
    Color,
    String,
    List,
    File,
    HasTraits,
    Bool,
    Int,
)
from traitsui.api import (
    View,
    VGroup,
    HGroup,
    spring,
    Label,
    Spring,
    EnumEditor,
    ObjectColumn,
    TableEditor,
    UItem,
)
from traitsui.editors.api import TextEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn

from pychron.core.helpers.strtools import to_bool, to_csv_str
from pychron.core.pychron_traits import HostStr
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.yaml import yload
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import FavoritesPreferencesHelper
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR


# IPREGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


def show_databases(
    kind, host, user, password, schema_identifier="AnalysisTbl", exclude=None
):
    records = []
    if kind == "mysql":
        import pymysql

        if exclude is None:
            exclude = ("information_schema", "performance_schema", "mysql")
        try:
            conn = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                connect_timeout=0.25,
                passwd=password,
                db="information_schema",
            )
            cur = conn.cursor()
            if schema_identifier:
                sql = (
                    '''select TABLE_SCHEMA from TABLES where TABLE_NAME="{}"'''.format(
                        schema_identifier
                    )
                )
            else:
                sql = "SHOW TABLES"

            cur.execute(sql)
            records = cur.fetchall()
        except BaseException as e:
            print("ezafa", e)
    elif kind == "mssql":
        import pymssql

        if exclude is None:
            exclude = ("master", "tempdb", "model", "msdb")
        try:
            conn = pymssql.connect(host, user, password, timeout=1)
            cur = conn.cursor()
            sql = "SELECT * FROM sys.databases"
            cur.execute(sql)
            records = cur.fetchall()
        except pymssql.OperationalError:
            pass

    names = [di[0] for di in records if di[0] not in exclude]
    return names


class ConnectionMixin(HasTraits):
    test_connection_button = Button
    # _test_connection_button = Button

    _connected_label = String("Not Tested")
    _connected_color = Color("orange")
    _adapter_klass = "pychron.database.core.database_adapter.DatabaseAdapter"
    _names = List
    _test_func = None

    def _reset_connection_label(self, d):
        def func():
            self._connected_label = "Not Tested"
            self._connected_color = "orange"

        if d:
            do_later(func)
        else:
            func()

    def _get_connection_dict(self):
        raise NotImplementedError

    def _get_adapter(self):
        args = self._adapter_klass.split(".")
        mod, klass = ".".join(args[:-1]), args[-1]
        mod = __import__(mod, fromlist=[klass])
        return getattr(mod, klass)

    def _test_connection(self, kw):
        klass = self._get_adapter()
        db = klass(**kw)
        if self._test_func:
            db.test_func = self._test_func

        c = db.connect(warn=False)
        e = db.connection_error

        return c, e

    def _test_connection_button_fired(self):
        kw = self._get_connection_dict()
        self._connected_color = "red"
        self._connected_label = "Not Connected"

        if kw is not None:
            c, e = self._test_connection(kw)
            if c:
                self._connected_color = "green"
                self._connected_label = "Connected"
            else:
                warning(
                    None,
                    "Not connected to database. {}. See log for more details".format(e),
                )
        else:
            warning(None, "Please select a connection to test")


class ConnectionFavoriteItem(HasTraits):
    enabled = Bool
    name = Str
    dbname = Str
    host = HostStr
    kind = Enum("mysql", "sqlite", "mssql", "postgres", NULL_STR)
    username = Str
    names = List
    password = Password
    schema_identifier = Str
    path = File
    default = Bool
    timeout = Int(5)

    attributes = (
        "name",
        "kind",
        "username",
        "host",
        "dbname",
        "password",
        "enabled",
        "default",
        "path",
        "timeout",
    )

    def __init__(self, schema_identifier="", attrs=None, kind=None):
        super(ConnectionFavoriteItem, self).__init__()
        self.schema_identifier = schema_identifier
        if kind is not None:
            self.kind = kind

        if attrs:
            attrs = attrs.split(",")

            try:
                (
                    self.name,
                    self.kind,
                    self.username,
                    self.host,
                    self.dbname,
                    self.password,
                ) = attrs
            except ValueError:
                try:
                    (
                        self.name,
                        self.kind,
                        self.username,
                        self.host,
                        self.dbname,
                        self.password,
                        enabled,
                    ) = attrs
                    self.enabled = to_bool(enabled)
                except ValueError:
                    try:
                        (
                            self.name,
                            self.kind,
                            self.username,
                            self.host,
                            self.dbname,
                            self.password,
                            enabled,
                            default,
                        ) = attrs

                        self.enabled = to_bool(enabled)
                        self.default = to_bool(default)
                    except ValueError:
                        try:
                            (
                                self.name,
                                self.kind,
                                self.username,
                                self.host,
                                self.dbname,
                                self.password,
                                enabled,
                                default,
                                path,
                            ) = attrs
                            self.enabled = to_bool(enabled)
                            self.default = to_bool(default)
                            self.path = path
                        except ValueError:
                            (
                                self.name,
                                self.kind,
                                self.username,
                                self.host,
                                self.dbname,
                                self.password,
                                enabled,
                                default,
                                path,
                                timeout,
                            ) = attrs
                            self.enabled = to_bool(enabled)
                            self.default = to_bool(default)
                            self.path = path
                            self.timeout = int(timeout)

            self.load_names()

    def load_names(self):
        if self.username and self.host and self.password:
            if self.schema_identifier:
                names = show_databases(
                    self.kind,
                    self.host,
                    self.username,
                    self.password,
                    self.schema_identifier,
                )
                self.names = names

    def to_string(self):
        attrs = [getattr(self, attr) for attr in self.attributes]
        return to_csv_str(attrs)

    # def to_string(self):
    #     attrs = [getattr(self, attr) for attr in ('name', 'kind', 'username', 'host',
    #                                               'dbname', 'password', 'enabled', 'default', 'path')]
    #     return to_csv_str(attrs)

    # return ','.join([str(getattr(self, attr)) for attr in ('name', 'kind', 'username', 'host',
    #                                                        'dbname', 'password', 'enabled', 'default', 'path')])

    def __repr__(self):
        return self.name


class ConnectionPreferences(FavoritesPreferencesHelper, ConnectionMixin):
    preferences_path = "pychron.database"
    add_favorite_path = Button
    add_favorite_shareable_archive = Button

    _fav_klass = ConnectionFavoriteItem
    _schema_identifier = None
    load_names_button = Button

    def __init__(self, *args, **kw):
        super(ConnectionPreferences, self).__init__(*args, **kw)

    def _add_favorite_shareable_archive_fired(self):
        dlg = FileDialog(
            action="open", wildcard="*.pz", default_directory=paths.data_dir
        )
        if dlg.open() == OK:
            if dlg.path:
                yd = yload(dlg.path)
                name = os.path.splitext(os.path.basename(dlg.path))[0]
                path = os.path.join(paths.offline_db_dir, "{}.sqlite".format(name))
                with open(path, "wb") as wfile:
                    wfile.write(yd["database"])

                item = self._fav_factory(kind="sqlite", path=path, enabled=True)
                item.trait_set(
                    **{
                        k: yd[k]
                        for k in [
                            "organization",
                            "meta_repo_name",
                        ]
                    }
                )
                try:
                    item.meta_repo_dir = yd["meta_repo_dirname"]
                except KeyError:
                    item.meta_repo_dir = "{}MetaData".format(item.organization)

                try:
                    item.name = yd["name"]
                except KeyError:
                    pass

                try:
                    item.repository_root = yd["repository_root"]
                except KeyError:
                    pass

                self._fav_items.append(item)
                self._set_favorites()
                item.default = True
                information(
                    None, "Please restart to complete the addition of this archive"
                )

    def _add_favorite_path_fired(self):
        dlg = FileDialog(action="open")
        if dlg.open() == OK:
            if dlg.path:
                self._fav_items.append(
                    self._fav_factory(kind="sqlite", path=dlg.path, enabled=True)
                )
                self._set_favorites()

    def _fav_factory(self, fav=None, **kw):
        f = self._fav_klass(self._schema_identifier, fav)
        f.trait_set(**kw)

        return f

    def _get_connection_dict(self):
        obj = self._selected
        if obj is not None:
            return dict(
                username=obj.username,
                host=obj.host,
                password=obj.password,
                name=obj.dbname,
                kind=obj.kind,
                timeout=obj.timeout,
            )

    def __selected_changed(self):
        self._reset_connection_label(True)

    def _load_names_button_fired(self):
        obj = self._selected
        if obj:
            obj.load_names()

    @on_trait_change("_fav_items:+")
    def fav_item_changed(self, obj, name, old, new):
        if name in ("username", "password"):
            obj.load_names()
        elif name == "default":
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
    category = "Database"

    def get_columns(self):
        cols = [
            CheckboxColumn(name="enabled"),
            CheckboxColumn(name="default"),
            ObjectColumn(name="kind"),
            ObjectColumn(name="name"),
            ObjectColumn(name="username"),
            ObjectColumn(
                name="password",
                format_func=lambda x: "*" * len(x),
                editor=TextEditor(password=True),
            ),
            ObjectColumn(name="host"),
            ObjectColumn(name="timeout"),
            ObjectColumn(
                name="dbname", label="Database", editor=EnumEditor(name="names")
            ),
            ObjectColumn(name="path", style="readonly"),
        ]
        return cols

    def get_buttons(self):
        return HGroup(
            icon_button_editor(
                "add_favorite", "database_add", tooltip="Add saved connection"
            ),
            icon_button_editor(
                "add_favorite_path", "dbs_sqlite", tooltip="Add sqlite database"
            ),
            icon_button_editor(
                "add_favorite_shareable_archive",
                "add_package",
                tooltip="Add a shareable archive",
            ),
            icon_button_editor(
                "delete_favorite", "delete", tooltip="Delete saved connection"
            ),
            icon_button_editor(
                "test_connection_button", "database_connect", tooltip="Test connection"
            ),
            icon_button_editor(
                "load_names_button",
                "arrow_refresh",
                enabled_when="load_names_enabled",
                tooltip="Load available database schemas on the selected server",
            ),
        )

    def get_fav_group(self, edit_view=None):
        cols = self.get_columns()
        editor = TableEditor(columns=cols, selected="_selected", sortable=False)
        if edit_view:
            editor.edit_view = edit_view
            editor.orientation = "vertical"
            editor.edit_view_height = 0.25

        fav_grp = VGroup(
            UItem("_fav_items", width=100, editor=editor),
            HGroup(
                self.get_buttons(),
                Spring(width=10, springy=False),
                Label("Status:"),
                CustomLabel(
                    "_connected_label",
                    label="Status",
                    weight="bold",
                    color_name="_connected_color",
                ),
                spring,
                show_labels=False,
            ),
        )
        return fav_grp

    def traits_view(self):
        fav_grp = self.get_fav_group()
        return View(fav_grp)


# ============= EOF =============================================
