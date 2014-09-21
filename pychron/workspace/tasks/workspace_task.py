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
import os

from pyface.tasks.action.schema import SToolBar
from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.workspace.tasks.actions import NewWorkspaceAction, OpenWorkspaceAction, CheckoutAnalysesAction
from pychron.workspace.tasks.panes import WorkspaceCentralPane, WorkspaceControlPane
from pychron.workspace.workspace_manager import ArArWorkspaceManager


class WorkspaceTask(BaseBrowserTask):

    tool_bars = [SToolBar(NewWorkspaceAction(),
                          OpenWorkspaceAction(),
                          CheckoutAnalysesAction())]
    workspace = Instance(ArArWorkspaceManager, ())

    def checkout_analyses(self):
        self.debug('checking out analyses')
        print self.analysis_table.analyses

    def new_workspace(self):
        self.debug('new workspace')

    def open_workspace(self):
        self.debug('open workspace')
        p='/Users/ross/Pychrondata_dev/data/workspaces/test'
        if not os.path.isdir(p):
            p = self.open_directory_dialog(default_directory=paths.workspace_root_dir)

        if p:
            self.workspace.create_repo(p)

    def create_central_pane(self):
        return WorkspaceCentralPane(model=self.workspace)

    def create_dock_panes(self):
        return [WorkspaceControlPane(),
                self._create_browser_pane()]
#============= EOF =============================================


