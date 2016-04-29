# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Str, Password
from traitsui.api import View, Item, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class GitHostPreferences(BasePreferencesHelper):
    username = Str
    password = Password
    oauth_token = Str
    default_remote_name = Str


class GitHubPreferences(GitHostPreferences):
    preferences_path = 'pychron.github'


class GitLabPreferences(GitHostPreferences):
    host = Str
    preferences_path = 'pychron.gitlab'


class GitHostPreferencesPane(PreferencesPane):
    def _cred_group(self):
        g = VGroup(VGroup(Item('username'),
                          Item('password'),
                          show_border=True, label='Basic'),
                   VGroup(Item('oauth_token', label='Token'),
                          show_border=True, label='OAuth'),
                   show_border=True, label='Credentials')
        return g

    def traits_view(self):
        v = View(self._cred_group())
        return v


class GitHubPreferencesPane(GitHostPreferencesPane):
    model_factory = GitHubPreferences
    category = 'GitHub'


class GitLabPreferencesPane(GitHostPreferencesPane):
    model_factory = GitLabPreferences
    category = 'GitLab'

    def traits_view(self):
        hg = VGroup(Item('host'))

        v = View(VGroup(self._cred_group(),
                        hg))
        return v

# ============= EOF =============================================
