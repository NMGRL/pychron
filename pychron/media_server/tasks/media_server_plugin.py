# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from envisage.ui.tasks.task_factory import TaskFactory

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.media_server.browser import MediaBrowser
from pychron.media_server.client import MediaClient
from pychron.media_server.tasks.media_server_task import MediaServerTask

# ============= standard library imports ========================
# ============= local library imports  ==========================

class MediaServerPlugin(BaseTaskPlugin):
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=MediaClient,
                                        factory=MediaClient
                                        )
        so1 = self.service_offer_factory(protocol=MediaBrowser,
                                        factory=MediaBrowser
                                        )
        return [so, so1]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.media_server',
                            factory=self._task_factory,
                            name='Media Server'),
                ]

    def _task_factory(self):
        client = MediaClient(
                             host='localhost',
                             use_cache=True,
                             cache_dir='/Users/ross/Sandbox/cache',
                             port=8008
                             )
        browser = MediaBrowser(client=client)
        browser.load_remote_directory('images')
        return MediaServerTask(browser=browser)
# ============= EOF =============================================
