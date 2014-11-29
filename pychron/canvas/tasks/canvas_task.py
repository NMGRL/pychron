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
import os

from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from traits.api import Instance


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.tasks.designer import Designer
from pychron.paths import paths
from pychron.canvas.tasks.panes import CanvasDesignerPane
from pychron.envisage.tasks.base_task import BaseTask


class OpenAction(TaskAction):
    name = 'Open'
    method = 'open'


class SaveAction(TaskAction):
    name = 'Save'
    method = 'save'


class CanvasDesignerTask(BaseTask):
    name = 'Canvas Designer'
    tool_bars = [SToolBar(OpenAction(),
                          SaveAction()
    )]

    designer = Instance(Designer)

    def _designer_default(self):
        return Designer()

    def open(self):
        print 'asfsfdsf open'
        p = os.path.join(paths.canvas2D_dir,
                         'canvas.xml'
        )
        self.designer.open_xml(p)

    def save(self):
        p = os.path.join(paths.canvas2D_dir,
                         'canvas.xml'
        )
        self.designer.save_xml(p)


    # ================================================================
    # Task interface
    # ================================================================
    def create_central_pane(self):
        return CanvasDesignerPane(model=self.designer)

        #def create_dock_panes(self):
        #    panes = []
        #    return panes

# ============= EOF =============================================
