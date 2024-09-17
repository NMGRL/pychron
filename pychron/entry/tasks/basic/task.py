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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem

from pychron.entry.basic_entry_manager import BasicEntryManager
from pychron.entry.tasks.basic.actions import SaveAction
from pychron.entry.tasks.basic.panes import BasicEntryPane, BasicEntryEditorPane
from pychron.envisage.tasks.base_task import BaseManagerTask


class BasicEntryTask(BaseManagerTask):
    id = "pychron.entry.basic.task"
    name = "Database"

    tool_bars = [SToolBar(SaveAction())]

    def prepare_destroy(self):
        self.manager.prepare_destroy()

    def save(self):
        self.manager.save()

    def create_central_pane(self):
        return BasicEntryPane(model=self.manager)

    def create_dock_panes(self):
        return [BasicEntryEditorPane(model=self.manager)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("pychron.basic.editor"))

    def _manager_default(self):
        dvc = self.application.get_service("pychron.dvc.dvc.DVC")
        return BasicEntryManager(dvc=dvc)


# ============= EOF =============================================
