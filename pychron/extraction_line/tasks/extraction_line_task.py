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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import ConsolePane
from pychron.envisage.tasks.wait_pane import WaitPane
from pychron.extraction_line.tasks.extraction_line_actions import SampleLoadingAction, AutoReloadAction
from pychron.extraction_line.tasks.extraction_line_pane import CanvasPane, GaugePane, \
    ExplanationPane
from pychron.envisage.tasks.base_task import BaseHardwareTask


class ExtractionLineTask(BaseHardwareTask):
    id = 'pychron.extraction_line'
    name = 'Extraction Line'
    wait_pane = Instance(WaitPane)

    def _tool_bars_default(self):
        tb = SToolBar(
            SampleLoadingAction(),
            # IsolateChamberAction(),
            # EvacuateChamberAction(),
            # FinishChamberChangeAction(),
            image_size=(16, 16))
        tb2 = SToolBar(AutoReloadAction())
        return [tb, tb2]

    def _default_layout_default(self):
        return TaskLayout(
            top=PaneItem('pychron.extraction_line.gauges'),
            left=PaneItem('pychron.extraction_line.explanation'),
            right=PaneItem('pychron.console'))

    def activated(self):
        self.manager.activate()

    def prepare_destroy(self):
        self.manager.deactivate()
        #         self.manager.closed(True)

    def create_central_pane(self):
        g = CanvasPane(model=self.manager)
        return g

    def create_dock_panes(self):
        self.wait_pane = WaitPane(model=self.manager.wait_group)
        panes = [GaugePane(model=self.manager),
                 ExplanationPane(model=self.manager),
                 ConsolePane(model=self.manager),
                 self.wait_pane
                 ]
        return panes

    # =======================================================================
    # toolbar actions
    # =======================================================================
    def do_sample_loading(self):
        self.manager.do_sample_loading()

    def enable_auto_reload(self):
        self.manager.enable_auto_reload()
# ============= EOF =============================================
