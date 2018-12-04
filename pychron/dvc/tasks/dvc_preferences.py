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
from traits.api import Str, Bool, Int
from traitsui.api import View, Item, HGroup, VGroup

from pychron.core.helpers.strtools import to_bool, to_csv_str
from pychron.core.pychron_traits import BorderVGroup
from pychron.database.tasks.connection_preferences import ConnectionPreferences, ConnectionPreferencesPane, \
    ConnectionFavoriteItem
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


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
        attrs = [getattr(self, attr) for attr in ('name', 'kind', 'username', 'host',
                                                  'dbname', 'password', 'enabled', 'default', 'path',
                                                  'organization', 'meta_repo_name', 'meta_repo_dir')]
        return to_csv_str(attrs)


class DVCConnectionPreferences(ConnectionPreferences):
    preferences_path = 'pychron.dvc.connection'
    _adapter_klass = 'pychron.dvc.dvc_database.DVCDatabase'
    _schema_identifier = 'AnalysisTbl'
    _fav_klass = DVCConnectionItem


class DVCConnectionPreferencesPane(ConnectionPreferencesPane):
    model_factory = DVCConnectionPreferences
    category = 'DVC'

    def traits_view(self):
        ev = View(Item('organization'),
                  Item('meta_repo_name'),
                  Item('meta_repo_dir'))
        fav_grp = self.get_fav_group(edit_view=ev)

        return View(fav_grp)


class DVCPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dvc'
    use_cocktail_irradiation = Bool
    use_cache = Bool
    max_cache_size = Int


class DVCPreferencesPane(PreferencesPane):
    model_factory = DVCPreferences
    category = 'DVC'

    def traits_view(self):
        v = View(VGroup(BorderVGroup(Item('use_cocktail_irradiation',
                                          tooltip='Use the special cocktail.json for defining the '
                                                  'irradiation flux and chronology',
                                          label='Use Cocktail Irradiation')),
                        BorderVGroup(HGroup(Item('use_cache', label='Enabled'),
                                            Item('max_cache_size', label='Max Size')),
                                     label='Cache')))
        return v


class DVCExperimentPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dvc.experiment'
    use_dvc_persistence = Bool


class DVCExperimentPreferencesPane(PreferencesPane):
    model_factory = DVCExperimentPreferences
    category = 'Experiment'

    def traits_view(self):
        v = View(BorderVGroup(Item('use_dvc_persistence', label='Use DVC Persistence'),
                              label='DVC'))
        return v


class DVCRepositoryPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dvc.repository'
    check_for_changes = Bool


class DVCRepositoryPreferencesPane(PreferencesPane):
    model_factory = DVCRepositoryPreferences
    category = 'Repositories'

    def traits_view(self):
        v = View(BorderVGroup(Item('check_for_changes', label='Check for Changes'),
                              label=''))
        return v
# ============= EOF =============================================
