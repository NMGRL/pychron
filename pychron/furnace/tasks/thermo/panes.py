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
from threading import Thread

from enable.component_editor import ComponentEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Button, Bool, Str
from traitsui.api import (
    View,
    Item,
    UItem,
    VGroup,
    HGroup,
    EnumEditor,
    spring,
    ButtonEditor,
    Tabbed,
)

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.lcd_editor import LCDEditor
from pychron.core.ui.led_editor import LEDEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ControlPane(TraitsDockPane):
    name = "Controls"
    id = "pychron.thermofurnace.controls"

    dump_sample_button = Button("Load")

    refresh_states_button = Button("Refresh")

    toggle_advanced_view_button = Button
    _advanced_view_state = Bool(False)

    disable_button = Button

    clear_sample_states_button = Button("Clear Dumped Samples")

    def _disable_button_fired(self):
        self.model.setpoint = 0

    def _dump_sample_button_fired(self):
        self.model.dump_sample()

    def _toggle_advanced_view_button_fired(self):
        self._advanced_view_state = not self._advanced_view_state

    def _refresh_states_button_fired(self):
        self.model.refresh_states()

    def _clear_sample_states_button_fired(self):
        self.model.clear_sample_states()

    def trait_context(self):
        return {
            "object": self.model,
            "pane": self,
            "tray_manager": self.model.stage_manager.tray_calibration_manager,
            "stage_manager": self.model.stage_manager,
        }

    def traits_view(self):
        # cali_grp = VGroup(UItem('tray_manager.calibrate',
        #                         enabled_when='stage_manager.stage_map_name',
        #                         editor=ButtonEditor(label_value='tray_manager.calibration_step')),
        #                   HGroup(Readonly('tray_manager.x', format_str='%0.3f'),
        #                          Readonly('tray_manager.y', format_str='%0.3f')),
        #                   Readonly('tray_manager.rotation', format_str='%0.3f'),
        #                   Readonly('tray_manager.scale', format_str='%0.4f'),
        #                   Readonly('tray_manager.error', format_str='%0.2f'),
        #                   UItem('tray_manager.calibrator', style='custom', editor=InstanceEditor()),
        #                   CustomLabel('tray_manager.calibration_help',
        #                               color='green',
        #                               height=75, width=300),
        #
        #                   show_border=True, label='Calibration')
        c_grp = VGroup(
            HGroup(
                Item("setpoint"),
                spring,
                icon_button_editor("pane.disable_button", "cancel"),
            ),
            VGroup(UItem("temperature_readback", editor=LCDEditor())),
            icon_button_editor(
                "start_record_button",
                "media-record",
                tooltip="Start recording",
                enabled_when="not _recording",
            ),
            icon_button_editor(
                "stop_record_button",
                "media-playback-stop",
                tooltip="Stop recording",
                enabled_when="_recording",
            ),
            label="Controller",
            show_border=True,
        )

        feeder_grp = VGroup(
            HGroup(
                Item("stage_manager.calibrated_position_entry", label="Hole"),
                icon_button_editor("pane.toggle_advanced_view_button", "cog"),
            ),
            # VGroup(Item('stage_manager.feeder.position', label='Position (units)'),
            #        Item('stage_manager.feeder.velocity'),
            #        Item('pane.feeder_set_home_button'),
            #        HGroup(icon_button_editor('pane.feeder_slew_positive', 'arrow_left'),
            #               icon_button_editor('pane.feeder_slew_negative', 'arrow_right'),
            #               icon_button_editor('pane.feeder_stop_button', 'cancel')),
            #        visible_when='pane._advanced_view_state'),
            show_border=True,
            label="Position",
        )

        dump_grp = HGroup(
            UItem(
                "pane.dump_sample_button",
                enabled_when="dump_sample_enabled",
                tooltip="Execute the complete sample loading procedure",
            ),
            show_border=True,
            label="Dump",
        )
        status_grp = HGroup(CustomLabel("status_txt", size=14))
        d1 = VGroup(status_grp, feeder_grp, dump_grp)

        d_grp = HGroup(d1, label="Dumper", show_border=True)

        g_grp = VGroup(
            Item("graph_scan_width", label="Scan Width (mins)"),
            HGroup(
                Item("graph_scale", label="Scale"),
                Item("graph_y_auto", label="Autoscale Y"),
                Item(
                    "graph_ymax",
                    label="Max",
                    format_str="%0.3f",
                    enabled_when="not graph_y_auto",
                ),
                Item(
                    "graph_ymin",
                    label="Min",
                    format_str="%0.3f",
                    enabled_when="not graph_y_auto",
                ),
            ),
            HGroup(
                icon_button_editor(
                    "clear_button", "clear", tooltip="Clear and reset graph"
                ),
                spring,
            ),
            HGroup(
                icon_button_editor(
                    "start_record_button",
                    "media-record",
                    tooltip="Start recording",
                    enabled_when="not _recording",
                ),
                icon_button_editor(
                    "stop_record_button",
                    "media-playback-stop",
                    tooltip="Stop recording",
                    enabled_when="_recording",
                ),
                icon_button_editor(
                    "add_marker_button", "flag", enabled_when="_recording"
                ),
                show_border=True,
                label="Record Scan",
            ),
            HGroup(
                icon_button_editor("snapshot_button", "camera"),
                show_border=True,
                label="Snapshot",
            ),
            label="Graph",
        )
        v = View(
            VGroup(c_grp, HGroup(Tabbed(d_grp, g_grp)))
        )  # HGroup(Tabbed(d_grp, v_grp, g_grp))))
        return v


class FurnacePane(TraitsTaskPane):
    def trait_context(self):
        return {
            "object": self.model,
            "pane": self,
            "tray_manager": self.model.stage_manager.tray_calibration_manager,
            "stage_manager": self.model.stage_manager,
        }

    def traits_view(self):
        canvas_grp = VGroup(
            HGroup(
                UItem(
                    "stage_manager.stage_map_name",
                    editor=EnumEditor(name="stage_manager.stage_map_names"),
                ),
                spring,
            ),
            UItem("stage_manager.canvas", style="custom", editor=ComponentEditor()),
        )

        v = View(VGroup(UItem("graph", style="custom"), canvas_grp))
        return v


class ExperimentFurnacePane(TraitsDockPane):
    name = "Furnace"
    id = "pychron.experiment.furnace"
    disable_button = Button

    def _disable_button_fired(self):
        self.model.setpoint = 0

    def traits_view(self):
        c_grp = VGroup(
            HGroup(
                Item("setpoint"),
                spring,
                icon_button_editor("pane.disable_button", "cancel"),
                Item("verbose_scan", label="Verbose Logging"),
            ),
            VGroup(
                UItem("temperature_readback", editor=LCDEditor(width=100, height=50))
            ),
            label="Controller",
            show_border=True,
        )

        v = View(c_grp)
        return v


# ============= EOF =============================================
