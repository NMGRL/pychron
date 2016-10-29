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


from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.social.gcal.gcal_manager import GCalManager
from pychron.social.gcal.tasks.preferences import GCalPreferencesPreferencesPane


class GoogleCalendarPlugin(BaseTaskPlugin):
    id = 'pychron.gcal.plugin'

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(protocol='pychron.social.gcal.gcal_manager.GCalManager',
                                        factory=GCalManager)
        return [so]

    # def _preferences_default(self):
    #     return ['file://{}'.format('')]
    #
    # def _task_extensions_default(self):
    #
    #     return [TaskExtension(SchemaAddition)]
    # def _tasks_default(self):
    #     return [TaskFactory(factory=self._task_factory,
    #                         protocol=FurnaceTask)]

    def _preferences_panes_default(self):
        return [GCalPreferencesPreferencesPane]

# ============= EOF =============================================
