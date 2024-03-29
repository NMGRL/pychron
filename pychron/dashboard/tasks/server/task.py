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
from __future__ import absolute_import
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dashboard.tasks.server.panes import (
    DashboardDevicePane,
    DashboardCentralPane,
)
from pychron.dashboard.server import DashboardServer
from pychron.envisage.tasks.base_task import BaseTask


class DashboardServerTask(BaseTask):
    name = "Dashboard Server"
    server = Instance(DashboardServer)

    def activated(self):
        self.server.activate()

    def create_central_pane(self):
        return DashboardCentralPane(model=self.server)

    def create_dock_panes(self):
        panes = [DashboardDevicePane(model=self.server)]
        return panes

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("pychron.dashboard.devices"))
        # ============= EOF =============================================
