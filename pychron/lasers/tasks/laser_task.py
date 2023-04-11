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
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter, Tabbed
from traits.api import Property

from pychron.envisage.tasks.base_task import BaseHardwareTask
from pychron.envisage.view_util import open_view
from pychron.lasers.pattern.pattern_maker_view import PatternMakerView

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.lasers.tasks.panes.ostech import (
    OsTechDiodeSupplementalPane,
    OsTechDiodeControlPane,
)
from pychron.pychron_constants import (
    FUSIONS_CO2,
    FUSIONS_DIODE,
    OSTECH_DIODE,
    TAP_DIODE,
)


class BaseLaserTask(BaseHardwareTask):
    power_map_enabled = Property(depends_on="manager")

    def _get_power_map_enabled(self):
        return self.manager.mode != "client"

    def activated(self):
        self.manager.opened()

        if self.manager.stage_manager:
            self.manager.stage_manager.keyboard_focus = True

    def prepare_destroy(self):
        self.manager.shutdown()

    def show_laser_script_executor(self):
        pass


class FusionsTask(BaseLaserTask):
    def _default_layout_default(self):
        return TaskLayout(
            left=PaneItem("{}.stage".format(self.id)),
            top=Splitter(
                PaneItem("{}.control".format(self.id), width=200),
                PaneItem("pychron.lasers.pulse", width=300),
                Tabbed(
                    PaneItem("pychron.lasers.optics"),
                    PaneItem("{}.supplemental".format(self.id)),
                ),
            ),
        )

    # ===============================================================================
    # action handlers
    # ===============================================================================
    def show_laser_script_executor(self):
        if self.manager:
            ex = self.manager.laser_script_executor
            open_view(ex)

    def show_motion_configure(self):
        if self.manager:
            self.manager.show_motion_controller_manager()

    def open_power_calibration(self):
        if self.manager:
            pc = self.manager.power_calibration_manager
            if pc:
                open_view(pc)

    def new_pattern(self):
        pm = PatternMakerView()
        open_view(pm)

    def open_pattern(self):
        pm = PatternMakerView()
        if pm.load_pattern():
            open_view(pm)

            # def open_pattern(self):
            #         if self.manager:
            #             self.manager.open_pattern_maker()
            #
            #     def new_pattern(self):
            #         if self.manager:
            #             self.manager.new_pattern_maker()
            #
            #     def execute_pattern(self):
            #         if self.manager:
            #             self.manager.execute_pattern()

            #     def open_power_map(self):
            #         if self.manager:
            #             pm = self.manager.get_power_map_manager()
            #             self.window.application.open_view(pm)

            # def test_degas(self):
            #     if self.manager:
            #         if self.manager.use_video:
            #             v = self.manager.degasser_factory()
            #             self.window.application.open_view(v)


class OsTechDiodeTask(BaseLaserTask):
    id = "pychron.ostech.diode"
    name = OSTECH_DIODE

    def create_central_pane(self):
        if self.manager.mode == "client":
            from pychron.lasers.tasks.panes.ostech import OsTechDiodeClientPane

            return OsTechDiodeClientPane(model=self.manager)
        else:
            from pychron.lasers.tasks.panes.ostech import OsTechDiodePane

            return OsTechDiodePane(model=self.manager)

    def create_dock_panes(self):
        if self.manager.mode == "client":
            return []
        else:
            from pychron.lasers.tasks.panes.ostech import OsTechDiodeStagePane

            # from pychron.lasers.tasks.panes.diode import FusionsDiodeControlPane
            # from pychron.lasers.tasks.panes.diode import FusionsDiodeSupplementalPane
            # from pychron.lasers.tasks.laser_panes import PulsePane
            # from pychron.lasers.tasks.laser_panes import OpticsPane
            # from pychron.lasers.tasks.laser_panes import AuxilaryGraphPane

            return [
                OsTechDiodeStagePane(model=self.manager),
                OsTechDiodeControlPane(model=self.manager),
                OsTechDiodeSupplementalPane(model=self.manager),
                # PulsePane(model=self.manager),
                # OpticsPane(model=self.manager),
                # AuxilaryGraphPane(model=self.manager)
            ]


class TAPDiodeTask(BaseLaserTask):
    id = "pychron.tap.diode"
    name = TAP_DIODE

    def create_central_pane(self):
        if self.manager.mode == "client":
            from pychron.lasers.tasks.panes.tap import TAPDiodeClientPane

            return TAPDiodeClientPane(model=self.manager)

        # else:
        #     from pychron.lasers.tasks.panes.ostech import OsTechDiodePane
        #     return OsTechDiodePane(model=self.manager)

    def create_dock_panes(self):
        if self.manager.mode == "client":
            return []
        # else:
        #     from pychron.lasers.tasks.panes.ostech import OsTechDiodeStagePane
        #
        #     # from pychron.lasers.tasks.panes.diode import FusionsDiodeControlPane
        #     # from pychron.lasers.tasks.panes.diode import FusionsDiodeSupplementalPane
        #     # from pychron.lasers.tasks.laser_panes import PulsePane
        #     # from pychron.lasers.tasks.laser_panes import OpticsPane
        #     # from pychron.lasers.tasks.laser_panes import AuxilaryGraphPane
        #
        #     return [
        #         OsTechDiodeStagePane(model=self.manager),
        #         OsTechDiodeControlPane(model=self.manager),
        #         OsTechDiodeSupplementalPane(model=self.manager),
        #         # PulsePane(model=self.manager),
        #         # OpticsPane(model=self.manager),
        #         # AuxilaryGraphPane(model=self.manager)
        #     ]
        #


class AblationCO2Task(BaseLaserTask):
    id = "pychron.ablation.co2"
    name = "Ablation CO2"

    def create_central_pane(self):
        from pychron.lasers.tasks.panes.ablation import AblationCO2ClientPane

        return AblationCO2ClientPane(model=self.manager)

    def create_dock_panes(self):
        return []


class ChromiumCO2Task(FusionsTask):
    id = "pychron.chromium.co2"
    name = "Chromium CO2"

    def create_central_pane(self):
        from pychron.lasers.tasks.panes.chromium import ChromiumCO2ClientPane

        return ChromiumCO2ClientPane(model=self.manager)

    def create_dock_panes(self):
        return []


class ChromiumDiodeTask(FusionsTask):
    id = "pychron.chromium.diode"
    name = "Chromium Diode"

    def create_central_pane(self):
        from pychron.lasers.tasks.panes.chromium import ChromiumDiodeClientPane

        return ChromiumDiodeClientPane(model=self.manager)

    def create_dock_panes(self):
        return []


class ChromiumUVTask(FusionsTask):
    id = "pychron.chromium.uv"
    name = "Chromium UV"

    def create_central_pane(self):
        from pychron.lasers.tasks.panes.chromium import ChromiumUVClientPane

        return ChromiumUVClientPane(model=self.manager)

    def create_dock_panes(self):
        return []


class FusionsCO2Task(FusionsTask):
    id = "pychron.fusions.co2"
    name = FUSIONS_CO2

    def create_central_pane(self):
        if self.manager.mode == "client":
            from pychron.lasers.tasks.panes.co2 import FusionsCO2ClientPane

            return FusionsCO2ClientPane(model=self.manager)
        else:
            from pychron.lasers.tasks.panes.co2 import FusionsCO2Pane

            return FusionsCO2Pane(model=self.manager)

    def create_dock_panes(self):
        if self.manager.mode == "client":
            return []
        else:
            from pychron.lasers.tasks.panes.co2 import FusionsCO2SupplementalPane
            from pychron.lasers.tasks.panes.co2 import FusionsCO2StagePane
            from pychron.lasers.tasks.panes.co2 import FusionsCO2ControlPane
            from pychron.lasers.tasks.laser_panes import PulsePane
            from pychron.lasers.tasks.laser_panes import OpticsPane
            from pychron.lasers.tasks.laser_panes import AuxilaryGraphPane

            return [
                FusionsCO2StagePane(model=self.manager),
                FusionsCO2ControlPane(model=self.manager),
                PulsePane(model=self.manager),
                OpticsPane(model=self.manager),
                FusionsCO2SupplementalPane(model=self.manager),
                AuxilaryGraphPane(model=self.manager),
            ]


class FusionsDiodeTask(FusionsTask):
    id = "fusions.diode"
    name = FUSIONS_DIODE

    def create_central_pane(self):
        if self.manager.mode == "client":
            from pychron.lasers.tasks.panes.diode import FusionsDiodeClientPane

            return FusionsDiodeClientPane(model=self.manager)
        else:
            from pychron.lasers.tasks.panes.diode import FusionsDiodePane

            return FusionsDiodePane(model=self.manager)

    def create_dock_panes(self):
        if self.manager.mode == "client":
            return []
        else:
            from pychron.lasers.tasks.panes.diode import FusionsDiodeStagePane
            from pychron.lasers.tasks.panes.diode import FusionsDiodeControlPane
            from pychron.lasers.tasks.panes.diode import FusionsDiodeSupplementalPane
            from pychron.lasers.tasks.laser_panes import PulsePane
            from pychron.lasers.tasks.laser_panes import OpticsPane
            from pychron.lasers.tasks.laser_panes import AuxilaryGraphPane

            return [
                FusionsDiodeStagePane(model=self.manager),
                FusionsDiodeControlPane(model=self.manager),
                FusionsDiodeSupplementalPane(model=self.manager),
                PulsePane(model=self.manager),
                OpticsPane(model=self.manager),
                AuxilaryGraphPane(model=self.manager),
            ]


class FusionsUVTask(FusionsTask):
    id = "fusions.uv"
    name = "Fusions UV"

    def create_central_pane(self):
        if self.manager.mode == "client":
            from pychron.lasers.tasks.panes.uv import FusionsUVClientPane

            klass = FusionsUVClientPane
        else:
            from pychron.lasers.tasks.panes.uv import FusionsUVPane

            klass = FusionsUVPane

        return klass(model=self.manager)

    def create_dock_panes(self):
        if self.manager.mode == "client":
            return []
        else:
            from pychron.lasers.tasks.panes.uv import FusionsUVStagePane
            from pychron.lasers.tasks.panes.uv import FusionsUVControlPane
            from pychron.lasers.tasks.panes.uv import FusionsUVSupplementalPane
            from pychron.lasers.tasks.laser_panes import OpticsPane

            return [
                FusionsUVStagePane(model=self.manager),
                FusionsUVControlPane(model=self.manager),
                FusionsUVSupplementalPane(model=self.manager),
                OpticsPane(model=self.manager),
            ]


# ============= EOF =============================================
