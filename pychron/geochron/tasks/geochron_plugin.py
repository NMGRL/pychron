# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.geochron.geochron_service import GeochronService
from pychron.geochron.tasks.preferences import GeochronPreferencesPane


class GeochronPlugin(BaseTaskPlugin):
    id = 'pychron.geochron.plugin'

    def _help_tips_default(self):
        return ['More information about Geochron is located at http://geochron.org/']

    def _service_offers_default(self):
        so1 = self.service_offer_factory(factory=GeochronService,
                                         protocol=GeochronService)
        return [so1]

    def _preferences_panes_default(self):
        return [GeochronPreferencesPane]

# ============= EOF =============================================
