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
import json
import os

from requests.exceptions import SSLError

from pychron.git.hosts import IGitHost
from pychron.git.hosts.github import GitHubService
from pychron.git.tasks.base_git_plugin import BaseGitPlugin
from pychron.git.tasks.flow import InstalledAppFlow
from pychron.git.tasks.githost_preferences import GitHubPreferencesPane
from pychron.paths import paths
from pychron.pychron_constants import STARTUP_MESSAGE_POSITION


class GitHubPlugin(BaseGitPlugin):
    name = "GitHub"
    service_klass = GitHubService
    id = "pychron.github.plugin"

    def start(self):
        p = self.application.preferences
        tok = p.get("pychron.github.oauth_token")
        if not tok:
            try:
                self.oauth_flow()
                return
            except SSLError:
                self.warning_dialog(
                    "OAuth authentication failed. Using old style authentication"
                )

        # use old style authenication
        # usr = p.get("pychron.github.username")
        # pwd = p.get("pychron.github.password")
        tok = p.get("pychron.github.oauth_token")
        org = p.get("pychron.github.organization")

        if not org:
            self.information_dialog(
                "Please set the organization that contains your data (e.g. NMGRLData) "
                "in Pychron's {} preferences".format(self.name),
                position=STARTUP_MESSAGE_POSITION,
            )
        if not tok:
            self.information_dialog(
                "Please set token in {} preferences".format(self.name),
                position=STARTUP_MESSAGE_POSITION,
            )
        else:
            service = self.application.get_service(IGitHost)
            service.set_authentication()
        # try:
        #     self.debug("checking for gh cli")
        #     subprocess.call(
        #         ["gh", "--version"],
        #         stdout=subprocess.DEVNULL,
        #     )
        #     self.debug("github authentication handled by gh")
        #     return
        # except FileNotFoundError:
        # self.oauth_flow()
        # if not tok and not (usr and pwd):
        #     self.information_dialog(
        #         "Please set user name and password or token in {} preferences".format(
        #             self.name
        #         ),
        #         position=STARTUP_MESSAGE_POSITION,
        #     )
        # else:
        #     service = self.application.get_service(IGitHost)
        #     service.set_authentication()

    def oauth_flow(self):
        # from google_auth_oauthlib.flow import InstalledAppFlow

        githubapp_config = {
            "installed": {
                "client_id": "Iv1.e4ea3100ace7882b",
                "client_secret": "00118d67ed990c72ac926f57b6c0a04bb2eb0120",
                "auth_uri": "https://github.com/login/oauth/authorize",
                "token_uri": "https://github.com/login/oauth/access_token",
            }
        }
        config = {
            "client_id": "05317d25974cd74eba4e",
            "client_secret": "be1fec163f573bfba2aea8dbd8b0452dad28bf95",
            "auth_uri": "https://github.com/login/oauth/authorize",
            "token_uri": "https://github.com/login/oauth/access_token",
        }

        p = paths.oauth_file
        if not os.path.isfile(p):
            flow = InstalledAppFlow()
            token = flow.flow(config, ["repo"])
            if token:
                with open(p, "w") as wfile:
                    json.dump(token, wfile)

    def _preferences_default(self):
        return self._preferences_factory("github")

    def _preferences_panes_default(self):
        return [GitHubPreferencesPane]


# ============= EOF =============================================
