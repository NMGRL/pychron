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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import

from requests.exceptions import SSLError

from pychron.git.hosts import GitHostService
from pychron.paths import paths


class GitHubService(GitHostService):
    preference_path = 'pychron.github'
    name = 'GitHub'
    _has_access = True

    @property
    def remote_url(self):
        return paths.github_url

    def up_to_date(self, organization, name, sha, branch='master'):
        cmd = '{}/repos/{}/{}/commits/{}'.format(paths.github_api_url, organization, name, branch)
        close_at_end = False
        if not self._session:
            self.new_session()
            close_at_end = True

        self._session.headers.update(ETag=sha, Accept='application/vnd.github.VERSION.sha')

        r = self._session.get(cmd)
        rsha = r.text
        ret = rsha != sha

        if close_at_end:
            self.close_session()
        return ret, rsha

    def get_repo(self, organization, name):
        cmd = '{}/repos/{}/{}'.format(paths.github_api_url, organization, name)
        resp = self._get(cmd)
        try:
            return resp[0]
        except IndexError:
            pass

    def test_api(self):
        ret, err = True, ''
        try:
            self._get(paths.github_api_url)
        except BaseException as e:
            ret = False
            err = e

        return ret, err

    def set_team(self, team, organization, repo, permission=None):
        if permission is None:
            permission = 'pull'

        team_id = self.get_team_id(team, organization)
        if team_id:
            cmd = '{}/teams/{}/repos/{}/{}'.format(paths.github_api_url, team_id, organization, repo)
            self._put(cmd, permission=permission)

    def get_team_id(self, name, organization):
        for td in self._get('{}/orgs/{}/teams'.format(paths.github_api_url,
                                                      organization)):
            if td['name'] == name:
                return td['id']

    def create_repo(self, name, organization, **kw):
        if self._has_access:
            try:
                cmd = '{}/orgs/{}/repos'.format(paths.github_api_url,
                                                organization)
                resp = self._post(cmd, name=name, **kw)
                if resp:
                    self.debug('Create repo response {}'.format(resp.status_code))
                    self._clear_cached_repo_names = True
                    return resp.status_code == 201
            except SSLError as e:
                self.warning('SSL Error. {}'.format(e))
                self._has_access = False
        else:
            return True

    def make_url(self, name, organization):
        return '{}/{}/{}.git'.format(paths.github_url,
                                     organization, name)

    def get_repos(self, organization):
        if self._has_access:
            try:
                cmd = '{}/orgs/{}/repos'.format(paths.github_api_url, organization)
                return self._get(cmd)
            except SSLError as e:
                self.warning('SSL Error. {}'.format(e))
                self._has_access = False
                return []
        else:
            return []

    def get_info(self, organization):
        cmd = '{}/{}'.format(paths.github_api_url, organization)
        return self._get(cmd)

    # private
    def _get_oauth_token(self):
        return 'token {}'.format(self.oauth_token)

# ============= EOF =============================================
