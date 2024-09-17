# ===============================================================================
# Copyright 2015 Jake Ross
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
from pyface.tasks.task_layout import TaskLayout, PaneItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.furnace.tasks.nmgrl.panes import FurnacePane, ControlPane
from pychron.furnace.tasks.task import BaseFurnaceTask


class NMGRLFurnaceTask(BaseFurnaceTask):
    id = "pychron.furnace.nmgrl.task"
    name = "Furnace"

    def create_dock_panes(self):
        return [ControlPane(model=self.manager)]

    def create_central_pane(self):
        return FurnacePane(model=self.manager)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("pychron.nmgrlfurnace.controls"))


# ============= EOF =============================================
