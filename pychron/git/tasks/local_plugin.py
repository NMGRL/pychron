# ===============================================================================
# Copyright 2019 ross
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
from pychron.envisage.tasks.base_plugin import BasePlugin
from pychron.git.hosts import IGitHost
from pychron.git.hosts.local import LocalGitHostService


class LocalGitPlugin(BasePlugin):
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=IGitHost, factory=self._factory)

        return [
            so,
        ]

    def _factory(self):
        c = LocalGitHostService()
        c.bind_preferences()
        return c


# ============= EOF =============================================
