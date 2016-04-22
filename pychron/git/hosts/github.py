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
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths


class GitHubService(GitHostService):
    preference_path = 'pychron.github'

    def clone_from(self, name, root, organization):
        url = self.make_url(name, organization)
        GitRepoManager.clone_from(url, root)

    def create_repo(self, name, organization, **kw):
        cmd = '{}/orgs/{}/repos'.format(paths.github_api_url,
                                        organization)
        return self._post(cmd, name=name, **kw)

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
