# ===============================================================================
# Copyright 2026 Jake Ross
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
from __future__ import absolute_import

from pychron.git.hosts.bridge import BridgeService
from pychron.git.tasks.base_git_plugin import BaseGitPlugin
from pychron.git.tasks.bridge_preferences import BridgePreferencesPane


class BridgePlugin(BaseGitPlugin):
    name = "Bridge"
    id = "pychron.bridge.plugin"
    service_klass = BridgeService

    def start(self):
        # Skip the BaseGitPlugin's GitHub-style auth probes — the bridge
        # uses GCP service account credentials, not GitHub tokens.
        p = self.application.preferences
        if not p.get("pychron.bridge.enabled"):
            self.debug("Bridge plugin loaded but disabled in preferences")
            return

        if not p.get("pychron.bridge.base_url"):
            self.warning("Bridge enabled but base_url is empty in preferences")

    def _preferences_panes_default(self):
        return [BridgePreferencesPane]


# ============= EOF =============================================
