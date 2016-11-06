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
from traitsui.api import View, Item, VGroup, UItem

from pychron.database.tasks.connection_preferences import ConnectionPreferences, ConnectionPreferencesPane
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class DVCPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dvc'
    meta_repo_name = Str
    organization = Str
    default_team = Str
    work_offline_user = Str
    work_offline_password = Password
    work_offline_host = Str


class DVCDBConnectionPreferences(ConnectionPreferences):
    preferences_path = 'pychron.dvc.db'
    _adapter_klass = 'pychron.dvc.dvc_database.DVCDatabase'
    _schema_identifier = 'AnalysisTbl'


class DVCDBConnectionPreferencesPane(ConnectionPreferencesPane):
    model_factory = DVCDBConnectionPreferences
    category = 'DVC'


class DVCPreferencesPane(PreferencesPane):
    model_factory = DVCPreferences
    category = 'DVC'

    def traits_view(self):
        org = VGroup(UItem('organization'),
                     Item('default_team', tooltip='Name of the GitHub Team to add to new repositories'),
                     label='Organization', show_border=True)
        meta = VGroup(UItem('meta_repo_name'), label='Meta', show_border=True)
        offline = VGroup(Item('work_offline_host', label='Host'),
                         Item('work_offline_user', label='Username'),
                         Item('work_offline_password', label='Password'),
                         label='Work Offline',
                         show_border=True)

        v = View(VGroup(VGroup(org, meta), label='Git',
                        show_border=True),
                 offline)
        return v


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
