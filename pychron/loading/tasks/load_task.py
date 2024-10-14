# ===============================================================================
# Copyright 2013 Jake Ross
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
from apptools.preferences.preference_binding import bind_preference
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import PaneItem, TaskLayout, VSplitter, HSplitter, Tabbed
from traits.api import Any
from traits.trait_types import DelegatesTo

from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.globals import globalv
from pychron.loading.tasks.actions import (
    SaveLoadingPDFAction,
    ConfigurePDFAction,
    SaveLoadingDBAction,
    GotoModeAction,
    GotoEntryModeAction,
    FootPedalModeAction,
    CheckTrayAction,
    MapTrayAction,
)
from pychron.loading.tasks.panes import (
    LoadPane,
    LoadControlPane,
    LoadTablePane,
    StageManagerPane,
    VideoPane,
    MachineVisionPane,
    CounterPane,
)

# ============= standard library imports ========================
# ============= local library imports  ==========================


class LoadingTask(BaseManagerTask):
    name = "Loading"
    load_pane = Any

    tool_bars = [
        SToolBar(SaveLoadingPDFAction(), ConfigurePDFAction()),
        SToolBar(SaveLoadingDBAction()),
        SToolBar(
            GotoModeAction(enabled_name="interaction_mode_enabled"),
            GotoEntryModeAction(enabled_name="interaction_mode_enabled"),
            FootPedalModeAction(enabled_name="interaction_mode_enabled"),
        ),
        # SToolBar(CheckTrayAction(),
        #          MapTrayAction())
    ]
    interaction_mode_enabled = DelegatesTo("manager")

    def activated(self):
        if self.manager.verify_database_connection(inform=True):
            if self.manager.load():
                self.manager.username = globalv.username
                if self.manager.setup():
                    bind_preference(
                        self.manager, "save_directory", "pychron.loading.save_directory"
                    )

    def _default_layout_default(self):
        return TaskLayout(
            left=Tabbed(
                PaneItem("pychron.loading.controls"),
                PaneItem("pychron.loading.machine_vision"),
            ),
            right=PaneItem("pychron.loading.video"),
            bottom=HSplitter(
                PaneItem("pychron.loading.positions"), PaneItem("pychron.loading.stage")
            ),
        )

    def prepare_destroy(self):
        self.manager.dvc.close_session()

    def create_dock_panes(self):
        control_pane = LoadControlPane(model=self.manager)
        table_pane = LoadTablePane(model=self.manager)
        stage_pane = StageManagerPane(model=self.manager)
        video_pane = VideoPane(model=self.manager.stage_manager)
        mv_pane = MachineVisionPane(model=self.manager.stage_manager)
        cpane = CounterPane(model=self.manager)
        return [control_pane, table_pane, stage_pane, video_pane, mv_pane, cpane]

    def create_central_pane(self):
        self.load_pane = LoadPane(model=self.manager)
        return self.load_pane

    def save(self):
        self.manager.save()

    # actions
    # def set_entry(self):
    #     self.manager.set_entry()
    #
    # def set_info(self):
    #     self.manager.set_info()
    #
    # def set_edit(self):
    #     self.manager.set_edit()
    def map_tray(self):
        self.manager.map_tray()

    def check_tray(self):
        self.manager.check_tray()

    def goto_mode(self):
        self.manager.set_interaction_mode("Goto")

    def goto_entry_mode(self):
        self.manager.set_interaction_mode("GotoEntry")

    def foot_pedal_mode(self):
        self.manager.set_interaction_mode("FootPedal")

    def configure_pdf(self):
        self.manager.configure_pdf()

    def save_loading_pdf(self):
        self.manager.save_pdf()

    def save_loading_db(self):
        self.manager.save(inform=True)

    def save_tray_pdf(self):
        self.manager.save_tray_pdf()

    # def generate_results(self):
    #     self.manager.generate_results()

    def _prompt_for_save(self):
        if self.manager.dirty:
            message = "You have unsaved changes. Save changes to Database?"
            ret = self._handle_prompt_for_save(message)
            if ret == "save":
                return self.manager.save()
            return ret
        return True


# ============= EOF =============================================
