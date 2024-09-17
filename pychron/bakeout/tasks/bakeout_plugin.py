# ===============================================================================
# Copyright 2024 ross
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

from pychron.bakeout.bakeout_manager import BakeoutManager
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class BakeoutPlugin(BaseTaskPlugin):
    id = "pychron.bakeout.plugin"
    name = "Bakeout"

    def _tasks_default(self):
        return [
            TaskFactory(
                id="pychron.bakeout.task",
                factory=self._task_factory,
                name="Bakeout",
                image="applications-science",
                task_group="hardware",
                accelerator="Ctrl+Shift+B",
            )
        ]

    def _service_offers_default(self):
        """ """
        so = self.service_offer_factory(protocol=BakeoutManager, factory=self._factory)
        return [so]

    def _factory(self):
        return BakeoutManager(application=self.application)

    def _task_factory(self):
        from pychron.bakeout.tasks.bakeout_task import BakeoutTask

        return BakeoutTask(
            application=self.application,
            manager=self.application.get_service(BakeoutManager),
        )

    def _managers_default(self):
        """ """
        return [
            dict(
                name="bakeout",
                plugin_name=self.name,
                manager=self.application.get_service(BakeoutManager),
            )
        ]


# ============= EOF =============================================
