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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.action.schema import SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.workspace.tasks.actions import ActivateWorkspaceAction, TestWorkspaceAction
from pychron.workspace.workspace_manager import WorkspaceManager


class WorkspacePlugin(BaseTaskPlugin):

    def _task_extensions_default(self):

        def make_actions(args):
            if len(args) == 3:
                mkw = {}
                i, f, p = args
            else:
                i, f, p, mkw = args

            return SchemaAddition(id=i, factory=f, path=p, **mkw)

        def workspace_menu():
            return SMenu(id='workspace.menu', name='Workspace')

        actions=[('workspace.menu', workspace_menu, 'MenuBar', {'before': 'tools.menu', 'after': 'view.menu'}),
                 ('pychron.workspace.activate', ActivateWorkspaceAction, 'MenuBar/workspace.menu'),
            ('pychron.workspace.test',TestWorkspaceAction, 'MenuBar/workspace.menu')]

        return [TaskExtension(actions=[make_actions(args) for args in actions])]

    def _service_offers_default(self):
        so = self.service_offer_factory(
            protocol=WorkspaceManager,
            factory=self._workspace_factory)
        return [so]

    def _workspace_factory(self):
        w = WorkspaceManager()
        return w

    def _tasks_default(self):
        wt = TaskFactory(factory=self._workspace_task_factory,
                         id='pychron.workspace',
                         name='Workspace',
                         # task_group=task_group,
                         accelerator='Ctrl+5',
                         # image=image,
                         # include_view_menu=include_view_menu or accelerator
        )
        tasks = [wt, ]
        return tasks

    def _workspace_task_factory(self):
        from pychron.workspace.tasks.workspace_task import WorkspaceTask

        central_db = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        return WorkspaceTask(manager=central_db)

    def _preferences_panes_default(self):
        return []

# ============= EOF =============================================



