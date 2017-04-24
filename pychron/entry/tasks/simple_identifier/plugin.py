# ===============================================================================
# Copyright 2017 ross
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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.entry.simple_identifier_manager import SimpleIdentifierManager
from pychron.entry.tasks.simple_identifier.actions import SimpleIdentifierAction
from pychron.entry.tasks.simple_identifier.task import SimpleIdentifierTask
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class SimpleIdentifierPlugin(BaseTaskPlugin):
    def _service_offers_default(self):
        so = self.service_offer_factory(factory=self._manager_factory,
                                        protocol=SimpleIdentifierManager)
        return [so, ]

    def _task_extensions_default(self):
        actions = [SchemaAddition(factory=SimpleIdentifierAction,
                                  path='MenuBar/entry.menu')]
        tes = [TaskExtension(actions=actions)]
        return tes

    def _tasks_default(self):
        return [TaskFactory(id='pychron.entry.simple_identifier.task',
                            factory=self._simple_identifier_task_factory,
                            include_view_menu=False), ]

    def _manager_factory(self):
        dvc = self.application.get_service('pychron.dvc.dvc.DVC')
        m = SimpleIdentifierManager(dvc=dvc)
        return m

    def _simple_identifier_task_factory(self):
        t = SimpleIdentifierTask()
        t.manager = self._manager_factory()
        return t

# ============= EOF =============================================
