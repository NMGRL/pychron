#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
# from pyface.tasks.task import Task
from pychron.hardware.tasks.hardware_pane import CurrentDevicePane, DevicesPane, InfoPane
from pyface.tasks.task_layout import PaneItem, TaskLayout, VSplitter
from pychron.envisage.tasks.base_task import BaseHardwareTask
#============= standard library imports ========================
#============= local library imports  ==========================

class HardwareTask(BaseHardwareTask):
    id = 'pychron.hardware'
    name = 'Hardware'

    def _default_layout_default(self):
        l = TaskLayout(left=VSplitter(
            PaneItem('hardware.devices'),
            PaneItem('hardware.info')
        )
        )
        return l

    def create_central_pane(self):
        pane = CurrentDevicePane(model=self.manager)
        return pane

    def create_dock_panes(self):
        return [DevicesPane(model=self.manager),
                InfoPane(model=self.manager)
        ]

    #============= EOF =============================================
