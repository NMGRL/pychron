# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import Str, Password, Bool
from traitsui.api import View, Item, VGroup, UItem, TextEditor, EnumEditor, TableEditor, HGroup, spring, Spring, Label
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.strtools import to_bool
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.database.tasks.connection_preferences import ConnectionPreferences, ConnectionPreferencesPane, \
    ConnectionFavoriteItem
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


#
# class DVCPreferences(BasePreferencesHelper):
#     preferences_path = 'pychron.dvc'
#     meta_repo_name = Str
#     meta_repo_dirname = Str
#     organization = Str
#     default_team = Str


class DVCConnectionItem(ConnectionFavoriteItem):
    organization = Str
    meta_repo_name = Str
    meta_repo_dir = Str

    def __init__(self, schema_identifier='', attrs=None, load_names=False):
        super(ConnectionFavoriteItem, self).__init__()
        self.schema_identifier = schema_identifier

        if attrs:
            attrs = attrs.split(',')
            try:
                (self.name, self.kind, self.username, self.host, self.dbname,
                 self.password, enabled, default, path) = attrs

            except ValueError:
                (self.name, self.kind, self.username, self.host, self.dbname,
                 self.password, enabled, default, self.path, self.organization,
                 self.meta_repo_name, self.meta_repo_dir) = attrs

            self.enabled = to_bool(enabled)
            self.default = to_bool(default)
            if load_names:
                self.load_names()

    def to_string(self):
        return ','.join([str(getattr(self, attr)) for attr in ('name', 'kind', 'username', 'host',
                                                               'dbname', 'password', 'enabled', 'default', 'path',
                                                               'organization', 'meta_repo_name', 'meta_repo_dir')])


class DVCConnectionPreferences(ConnectionPreferences):
    preferences_path = 'pychron.dvc.connection'
    _adapter_klass = 'pychron.dvc.dvc_database.DVCDatabase'
    _schema_identifier = 'AnalysisTbl'
    _fav_klass = DVCConnectionItem


class DVCConnectionPreferencesPane(ConnectionPreferencesPane):
    model_factory = DVCConnectionPreferences
    category = 'DVC'

    def traits_view(self):
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

        ev = View(Item('organization'),
                  Item('meta_repo_name'),
                  Item('meta_repo_dir'))

        fav_grp = VGroup(UItem('_fav_items',
                               width=100,
                               editor=TableEditor(columns=cols,
                                                  selected='_selected',
                                                  sortable=False,
                                                  edit_view=ev)),
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

        return View(fav_grp)


# class DVCPreferencesPane(PreferencesPane):
#     model_factory = DVCPreferences
#     category = 'DVC'
#
#     def traits_view(self):
#         org = VGroup(UItem('organization', resizable=True),
#                      Item('default_team', tooltip='Name of the GitHub Team to add to new repositories'),
#                      label='Organization', show_border=True)
#         meta = VGroup(Item('meta_repo_name', label='MetaData Repository Name',
#                            tooltip='Name of repository on GitHub',
#                            resizable=True),
#                       Item('meta_repo_dirname',
#                            label='MetaData Directory Name',
#                            tooltip='Name of local MetaData directory that links to the MetaData repository.'
#                                    'Leave blank if you do not understand'),
#                       label='MetaData Repo', show_border=True)
#
#         v = View(VGroup(VGroup(org, meta), label='Git',
#                         show_border=True))
#         return v


class DVCExperimentPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dvc.experiment'
    use_dvc_persistence = Bool


class DVCExperimentPreferencesPane(PreferencesPane):
    model_factory = DVCExperimentPreferences
    category = 'Experiment'

    def traits_view(self):
        v = View(VGroup(Item('use_dvc_persistence', label='Use DVC Persistence'),
                        label='DVC', show_border=True))
        return v

# ============= EOF =============================================
