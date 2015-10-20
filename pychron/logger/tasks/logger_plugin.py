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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.logger.tasks.actions import LogViewerAction, CurrentLogViewerAction
from pychron.logger.tasks.logger_task import LoggerTask


# ============= standard library imports ========================
# ============= local library imports  ==========================

class LoggerPlugin(BaseTaskPlugin):
    id = 'pychron.logger'
    name = 'Logger'

    def _tasks_default(self):
        return [TaskFactory(id=self.id,
                            factory=self._task_factory,
                            name='Logger')]

    def _task_factory(self):
        return LoggerTask()

    def _task_extensions_default(self):
        return [TaskExtension(actions=[SchemaAddition(factory=LogViewerAction,
                                                      path='MenuBar/help.menu'),
                                       SchemaAddition(factory=CurrentLogViewerAction,
                                                      path='MenuBar/help.menu')])]

# ============= EOF =============================================
