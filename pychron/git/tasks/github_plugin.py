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
from pychron.git.hosts.github import GitHubService
from pychron.git.tasks.base_git_plugin import BaseGitPlugin
from pychron.git.tasks.githost_preferences import GitHubPreferencesPane


class GitHubPlugin(BaseGitPlugin):
    name = "GitHub"
    service_klass = GitHubService
    id = "pychron.github.plugin"

    def _preferences_default(self):
        return self._preferences_factory("github")

    def _preferences_panes_default(self):
        return [GitHubPreferencesPane]


# ============= EOF =============================================
