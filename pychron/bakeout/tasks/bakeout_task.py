# ===============================================================================
# Copyright 2024 ross
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
from pyface.tasks.task_layout import TaskLayout, PaneItem

from pychron.bakeout.tasks.bakeout_panes import BakeoutGraphPane, BakeoutControlPane
from pychron.envisage.tasks.base_task import BaseManagerTask


class BakeoutTask(BaseManagerTask):

    def create_central_pane(self):
        return BakeoutGraphPane(model=self.manager)

    def create_dock_panes(self):
        control = BakeoutControlPane(model=self.manager)
        return [control]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("pychron.bakeout.control"))


# ============= EOF =============================================
