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
import base64

from apptools.preferences.preference_binding import bind_preference
from traits.api import Str, Interface, Password, provides
# ============= standard library imports ========================
import json
import requests
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class IGitHost(Interface):
    def bind_preferences(self):
        pass

    def clone_from(self, name, root, organization):
        pass

    def create_repo(self, name, **kw):
        pass

    def make_url(self, name, organization=None):
        pass

    def get_repository_names(self, organization=None):
        pass

    def test_connection(self, organization=None):
        pass

    def get_repos(self, org):
        pass

    def get_info(self, org):
        pass


@provides(IGitHost)
class GitHostService(Loggable):
    username = Str
    password = Password
    preference_path = ''
    oauth_token = Str

    def bind_preferences(self):
        bind_preference(self, 'username', '{}.username'.format(self.preference_path))
        bind_preference(self, 'password', '{}.password'.format(self.preference_path))
        bind_preference(self, 'oauth_token', '{}.oauth_token'.format(self.preference_path))

    def get_repository_names(self, organization):
        return [repo['name'] for repo in self.get_repos(organization)]

    def test_connection(self, organization):
        return bool(self.get_info(organization))

    def get_repos(self, org):
        pass

    def get_info(self, org):
        pass

    # private
    def _get(self, cmd):
        headers = self._get_authorization()
        doc = requests.get(cmd, headers=headers)
        self.debug('GET {}'.format(doc.text))
        return json.loads(doc.text)

    def _post(self, cmd, **payload):
        headers = self._get_authorization()
        r = requests.post(cmd, data=json.dumps(payload), headers=headers)
        return r

    def _get_oauth_token(self):
        raise NotImplementedError

    def _get_authorization(self):
        if self.oauth_token:
            auth = self._get_oauth_token()
        else:
            auth = base64.encodestring('{}:{}'.format(self.username,
                                                      self.password)).replace('\n', '')
            auth = 'Basic {}'.format(auth)

        return {"Authorization": auth}

# ============= EOF =============================================
