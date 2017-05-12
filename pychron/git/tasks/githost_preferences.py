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
import requests
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Password, Button, Color
from traitsui.api import View, Item, VGroup, HGroup

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, test_connection_item
from pychron.git.hosts import authorization
from pychron.globals import globalv


class GitHostPreferences(BasePreferencesHelper):
    username = Str
    password = Password
    oauth_token = Str
    default_remote_name = Str

    test_connection = Button
    _remote_status = Str
    _remote_status_color = Color

    def _test_connection_fired(self):
        self._remote_status_color = 'red'
        self._remote_status = 'Invalid'
        try:
            header = authorization(self.username, self.password, self._token)

            resp = requests.get(self._url,
                                headers=header,
                                verify=globalv.cert_file)

            if resp.status_code == 200:
                self._remote_status = 'Valid'
                self._remote_status_color = 'green'
        except BaseException, e:
            print 'exception', e, self._url


class GitHubPreferences(GitHostPreferences):
    preferences_path = 'pychron.github'

    @property
    def _url(self):
        return 'https://api.github.com/'

    @property
    def _token(self):
        if self.oauth_token:
            return 'token {}'.format(self.oauth_token)


class GitLabPreferences(GitHostPreferences):
    host = Str
    preferences_path = 'pychron.gitlab'

    @property
    def _url(self):
        return 'https://{}'.format(self.host)

    @property
    def _token(self):
        if self.oauth_token:
            return 'Bearer {}'.format(self.oauth_token)


class GitHostPreferencesPane(PreferencesPane):
    def _cred_group(self):
        g = VGroup(VGroup(Item('username'),
                          Item('password'),
                          show_border=True, label='Basic'),
                   VGroup(Item('oauth_token', label='Token'),
                          show_border=True, label='OAuth'),
                   HGroup(test_connection_item(),
                          CustomLabel('_remote_status',
                                      width=50,
                                      color_name='_remote_status_color')),
                   show_border=True, label='Credentials')
        return g

    def traits_view(self):
        v = View(self._cred_group(),
                 Item('default_remote_name', label='Default Remote'))
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
