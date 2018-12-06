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
import base64
import subprocess

import requests
# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Str, Interface, Password, provides, Dict

from pychron import json
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.regex import GITREFREGEX


class IGitHost(Interface):
    def bind_preferences(self):
        pass

    def test_api(self):
        pass

    def clone_from(self, name, root, organization):
        pass

    def set_team(self, team, organization, permission=None):
        pass

    def create_repo(self, name, **kw):
        pass

    def make_url(self, name, organization):
        pass

    def get_repository_names(self, organization):
        pass

    def test_connection(self, organization):
        pass

    def get_repos(self, organization):
        pass

    def get_info(self, organization):
        pass

    def remote_exists(self, name):
        pass


class CredentialException(BaseException):
    def __init__(self, d):
        self._auth = d['Authorization']

    def __str__(self):
        return 'Invalid user/password combination. {}'.format(self._auth)


def authorization(username, password, oauth_token):
    if oauth_token:
        auth = oauth_token
    else:
        auth = '{}:{}'.format(username, password).encode('utf-8')
        auth = base64.encodebytes(auth)
        auth = auth.replace(b'\n', b'')
        auth = 'Basic {}'.format(auth)

    return {"Authorization": auth}


@provides(IGitHost)
class GitHostService(Loggable):
    username = Str
    password = Password
    preference_path = ''
    oauth_token = Str
    default_remote_name = Str
    remote_url = Str
    _cached_repo_names = Dict
    _clear_cached_repo_names = False
    _session = None

    def bind_preferences(self):
        bind_preference(self, 'username', '{}.username'.format(self.preference_path))
        bind_preference(self, 'password', '{}.password'.format(self.preference_path))
        bind_preference(self, 'oauth_token', '{}.oauth_token'.format(self.preference_path))
        bind_preference(self, 'default_remote_name', '{}.default_remote_name'.format(self.preference_path))

    def up_to_date(self, organization, name, sha, branch='master'):
        pass

    def remote_exists(self, organization, name):
        try:
            cmd = ['git', 'ls-remote', '{}/{}/{}'.format(self.remote_url, organization, name)]
            self.debug('remote exists cmd={}'.format(' '.join(cmd)))
            out = subprocess.check_output(cmd)
            self.debug('remote exists: out={}'.format(out))
            if out:
                ret = GITREFREGEX.match(out.decode())
            else:
                ret = self.manual_remote_exists(organization, name)
        except subprocess.CalledProcessError:
            ret = self.manual_remote_exists(organization, name)
        return ret

    def manual_remote_exists(self, organization, name):
        repo = self.get_repo(organization, name)
        if repo:
            return repo.get('name', '').lower() == name.lower()

    def get_repo(self, organization, name):
        raise NotImplementedError

    def test_api(self):
        raise NotImplementedError

    def make_url(self):
        raise NotImplementedError

    def get_repository_names(self, organization):
        repos = self.get_repos(organization)
        return [repo['name'] for repo in repos]

    def test_connection(self, organization):
        return bool(self.get_info(organization))

    def clone_from(self, name, root, organization):
        url = self.make_url(name, organization)
        GitRepoManager.clone_from(url, root)

    def get_repos(self, org):
        pass

    def get_info(self, org):
        pass

    # private
    def _get(self, cmd, verbose=False):

        def func(s):
            s.headers.update(self._get_authorization())
            if globalv.cert_file:
                s.verify = globalv.cert_file

            def _rget(ci):
                r = s.get(ci)
                if r.status_code == 401:
                    raise CredentialException(self._get_authorization())

                d = json.loads(r.text)

                result = []
                if isinstance(d, list):
                    result.extend(d)
                else:
                    result.append(d)

                try:
                    dd = _rget(r.links['next']['url'])
                except KeyError:
                    return result

                if isinstance(dd, list):
                    result.extend(dd)
                else:
                    result.append(dd)
                return result

            return _rget(cmd)

        if self._session:
            return func(self._session)
        else:
            with requests.Session() as s:
                return func(s)

    def new_session(self):
        self._session = requests.Session()
        self._session.headers.update(self._get_authorization())

    def close_session(self):
        self._session.close()
        self._session = None

    def _post(self, cmd, **payload):
        headers = self._get_authorization()
        kw = {}
        if globalv.cert_file:
            kw['verify'] = globalv.cert_file

        r = requests.post(cmd, data=json.dumps(payload), headers=headers, **kw)
        return r

    def _put(self, cmd, **payload):
        headers = self._get_authorization()
        kw={}
        if globalv.cert_file:
            kw['verify'] = globalv.cert_file

        r = requests.put(cmd, data=json.dumps(payload), headers=headers, **kw)
        return r

    def _get_oauth_token(self):
        raise NotImplementedError

    def _get_authorization(self):
        token = None
        if self.oauth_token:
            token = self._get_oauth_token()
        return authorization(self.username, self.password, token)
        # if self.oauth_token:
        #     auth = self._get_oauth_token()
        # else:
        #     auth = base64.encodestring('{}:{}'.format(self.username,
        #                                               self.password)).replace('\n', '')
        #     auth = 'Basic {}'.format(auth)
        #
        # return {"Authorization": auth}

# ============= EOF =============================================
