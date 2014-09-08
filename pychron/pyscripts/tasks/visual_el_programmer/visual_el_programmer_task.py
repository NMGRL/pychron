#===============================================================================
# Copyright 2014 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.actions import GenericSaveAction, GenericSaveAsAction
from pychron.envisage.tasks.base_task import BaseTask
from pychron.pyscripts.extraction_line_script_writer import ExtractionLineScriptWriter
from pychron.pyscripts.tasks.visual_el_programmer.panes import CentralPane, ControlPane


class VisualElProgrammerTask(BaseTask):
    model = Instance(ExtractionLineScriptWriter, ())
    tool_bars = [SToolBar(GenericSaveAction(), GenericSaveAsAction())]

    def activated(self):
        self.model.set_default_states()

    def new(self):
        self.model.new()
        return True

    def open(self, path=None):
        return self.model.open_file(path)

    def save_as(self):
        self.model.save_as()

    def save(self):
        self.model.save()

    def create_central_pane(self):
        return CentralPane(model=self.model)

    def create_dock_panes(self):
        return [ControlPane(model=self.model)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.pyscript.visual.control'))

#============= EOF =============================================
