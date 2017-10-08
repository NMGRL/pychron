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

from envisage.ui.tasks.task_factory import TaskFactory

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.media_storage.manager import MediaStorageManager
from pychron.media_storage.tasks.preferences import MediaStoragePreferencesPane
from pychron.media_storage.tasks.task import MediaStorageTask


class MediaStoragePlugin(BaseTaskPlugin):
    name = 'Media Storage'
    id = 'pychron.media_storage.plugin'

    def _media_storage_factory(self):
        ms = MediaStorageTask(application=self.application)
        return ms

    def _media_storage_manager_factory(self):
        msm = MediaStorageManager()
        return msm

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=MediaStorageManager,
                                        factory=self._media_storage_manager_factory)
        return [so]

    def _preferences_panes_default(self):
        return [MediaStoragePreferencesPane]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.media_storage.task_factory',
                            include_view_menu=False,
                            factory=self._media_storage_factory)]

# ============= EOF =============================================
