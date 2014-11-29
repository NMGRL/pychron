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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.tasks.canvas_task import CanvasDesignerTask
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class CanvasDesignerPlugin(BaseTaskPlugin):
    id = 'pychron.canvas_designer.plugin'


    def _my_task_extensions_default(self):
        return [TaskExtension(actions=[])]

    def _tasks_default(self):
        ts = [TaskFactory(id='pychron.canvas_designer',
                          name='Canvas Designer',
                          factory=self._task_factory,
                          accelerator='Ctrl+Shift+D',
        )]
        return ts

    def _task_factory(self):
        t = CanvasDesignerTask()
        return t

    def _preferences_panes_default(self):
        return []

# ============= EOF =============================================
