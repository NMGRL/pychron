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
from apptools.preferences.preference_binding import bind_preference
from traits.api import Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.git.hosts import GitHostService


class GitLabService(GitHostService):
    host = Str
    preference_path = 'pychron.gitlab'
    name = 'GitLab'

    @property
    def remote_url(self):
        return self.host

    def bind_preferences(self):
        super(GitLabService, self).bind_preferences()
        bind_preference(self, 'host', '{}.host'.format(self.preference_path))

    def set_team(self, team, organization, repo, permission=None):
        pass

    def create_repo(self, name, organization, **kw):
        cmd = '{}/orgs/{}/repos'.format(self.host,
                                        organization)
        resp = self._post(cmd, name=name, **kw)
        if resp:
            self.debug('Create repo response {}'.format(resp.status_code))
            return resp.status_code == 201

    def make_url(self, name, organization):
        return 'http://{}/{}/{}.git'.format(self.host, organization, name)

    def get_repos(self, organization):
        cmd = '{}/groups/{}/projects'.format(self.host, organization)
        return self._get(cmd)

    def get_info(self, organization):
        cmd = '{}/groups/{}'.format(self.host, organization)
        return self._get(cmd)

    # private
    def _get_oauth_token(self):
        return 'Bearer {}'.format(self.oauth_token)
# ============= EOF =============================================
