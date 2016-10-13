# ===============================================================================
# Copyright 2015 Jake Ross
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
from pychron.repo.igsn import IGSNRepository

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from zobs.repo.tasks.preferences import IGSNPreferencesPane


class IGSNPlugin(BaseTaskPlugin):
    id = 'pychron.igsn.plugin'

    def _help_tips_default(self):
        return ['More information about IGSN is located at http://www.geosamples.org/']

    def _service_offers_default(self):
        so1 = self.service_offer_factory(factory=IGSNRepository,
                                         protocol=IGSNRepository)
        return [so1]

    def _preferences_panes_default(self):
        return [IGSNPreferencesPane]

# ============= EOF =============================================
