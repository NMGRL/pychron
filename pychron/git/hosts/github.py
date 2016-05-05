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
from pychron.git.hosts import GitHostService
from pychron.paths import paths


class GitHubService(GitHostService):
    preference_path = 'pychron.github'

    @property
    def remote_url(self):
        return paths.github_url

    def test_api(self):
        ret, err = True, ''
        try:
            self._get(paths.github_api_url)
        except BaseException, e:
            ret = False
            err = e

        return ret, err

    def set_team(self, team, organization, repo, permission=None):
        if permission is None:
            permission = 'pull'

        team_id = self.get_team_id(team)
        if team_id:
            cmd = 'teams/{}/repos/{}/{}'.format(team_id, organization, repo)
            self._put(cmd, permission=permission)

    def get_team_id(self, name, organization):
        for td in self._get('orgs/{}/teams'.format(organization)):
            if td['name'] == name:
                return td['id']

    def create_repo(self, name, organization, **kw):
        cmd = '{}/orgs/{}/repos'.format(paths.github_api_url,
                                        organization)
        resp = self._post(cmd, name=name, **kw)
        if resp:
            self.debug('Create repo response {}'.format(resp.status_code))
            return resp.status_code == 201

    def make_url(self, name, organization):
        return '{}/{}/{}.git'.format(paths.github_url,
                                     organization, name)

    def get_repos(self, organization):
        cmd = '{}/orgs/{}/repos'.format(paths.github_api_url, organization)
        return self._get(cmd)

    def get_info(self, organization):
        cmd = '{}/{}'.format(paths.github_api_url, organization)
        return self._get(cmd)

    # private
    def _get_oauth_token(self):
        return 'token {}'.format(self.oauth_token)

# ============= EOF =============================================
