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
from pyface.tasks.action.task_action import TaskAction
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action
from pychron.envisage.resources import icon


class ActivateWorkspaceAction(Action):
    name = 'Activate Workspace'
    def perform(self, event):
        app = event.task.application
        man = app.get_service('pychron.workspace.workspace_manager.WorkspaceManager')
        man.open_workspace()


class TestWorkspaceAction(Action):
    name = 'Test'
    accelerator = 'Ctrl+t'
    def perform(self, event):
        app = event.task.application
        man = app.get_service('pychron.workspace.workspace_manager.WorkspaceManager')
        man.open_workspace()

        task = app.open_task('pychron.recall')
        task.recall(task.analysis_table.analyses[:1])

class NewWorkspaceAction(TaskAction):
    name = 'New Workspace'
    method = 'new_workspace'
    image = icon('add')


class OpenWorkspaceAction(TaskAction):
    name = 'Open Workspace'
    method = 'open_workspace'
    image = icon('document-open')


class CheckoutAnalysesAction(TaskAction):
    name = 'Checkout Analyses'
    method = 'checkout_analyses'
    image = icon('database_go')


class AddBranchAction(TaskAction):
    name = 'Add Branch'
    method = 'add_branch'
    image = icon('add')


class TestModificationAction(TaskAction):
    name = 'Test'
    method = 'test_modification'


class TagBranchAction(TaskAction):
    name = 'Tag Branch'
    method = 'tag_branch'


class PullAction(TaskAction):
    name = 'Pull'
    method = 'pull'
    image = icon('arrow_down')


class PushAction(TaskAction):
    name = 'Push'
    method = 'push'
    image = icon('arrow_up')


class CommitChangesAction(TaskAction):
    name = 'Commit Changes'
    method = 'commit_changes'
    # image = icon('arrow_up')

#============= EOF =============================================



