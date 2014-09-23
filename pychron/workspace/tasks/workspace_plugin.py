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
#============= standard library imports ========================
#============= local library imports  ==========================
from envisage.ui.tasks.task_factory import TaskFactory

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class WorkspacePlugin(BaseTaskPlugin):
    def _tasks_default(self):
        wt = TaskFactory(factory=self._workspace_task_factory, name='Workspace',
                         # task_group=task_group,
                         accelerator='Ctrl+5',
                         # image=image,
                         # include_view_menu=include_view_menu or accelerator
                        )
        tasks = [wt,]
        return tasks

    def _workspace_task_factory(self):
        from pychron.workspace.tasks.workspace_task import WorkspaceTask
        central_db = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        return WorkspaceTask(manager=central_db)

    def _preferences_panes_default(self):
        return []

#============= EOF =============================================



