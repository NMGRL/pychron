# ===============================================================================
# Copyright 2014 Jake Ross
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
from envisage.ui.tasks.task_factory import TaskFactory
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.labbook.tasks.preferences import LabBookPreferencesPane


class LabBookPlugin(BaseTaskPlugin):
    name = 'LabBook'
    def _labbook_factory(self):
        from pychron.labbook.tasks.labbook_task import LabBookTask
        t=LabBookTask()
        return t

    def _tasks_default(self):
        tasks = [TaskFactory(id='pychron.labbook',
                             factory=self._labbook_factory,
                             name='LabBook')]
        return tasks

    def _preferences_panes_default(self):
        return [LabBookPreferencesPane]

#============= EOF =============================================



