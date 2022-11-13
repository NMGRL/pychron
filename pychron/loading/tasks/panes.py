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
from enable.component_editor import ComponentEditor
from pyface.action.menu_manager import MenuManager
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Int, Property, Instance
from traitsui.api import (
    View,
    UItem,
    Item,
    VGroup,
    TabularEditor,
    HGroup,
    spring,
    EnumEditor,
    Tabbed,
    Handler,
    CheckListEditor,
)
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.core.helpers.traitsui_shortcuts import okcancel_view, VFold, rfloatitem
from pychron.core.pychron_traits import BorderHGroup
from pychron.core.ui.button_editor import ButtonEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.image_editor import ImageEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.core.ui.table_configurer import TableConfigurer, TableConfigurerHandler
from pychron.core.ui.video_editor import VideoEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class PositionsAdapter(TabularAdapter, ConfigurableMixin):
    columns = [
        ("Identifier", "identifier"),
        ("Irradiation", "irradiation_str"),
        ("Sample", "sample"),
        ("Material", "material"),
        ("Position", "position"),
        ("Weight", "weight"),
        ("N. Xtals", "nxtals"),
        ("Note", "note"),
    ]
    all_columns = [
        ("Identifier", "identifier"),
        ("Packet", "packet"),
        ("Irradiation", "irradiation_str"),
        ("Sample", "sample"),
        ("Material", "material"),
        ("Position", "position"),
        ("Weight", "weight"),
        ("N. Xtals", "nxtals"),
        ("Note", "note"),
    ]
    font = "arial 12"
    identifier_width = Int(80)
    irradiation_str_width = Int(80)
    sample_width = Int(80)
    position_str_width = Int(80)
    configure_name = "configure_position_table"

    def get_menu(self, obj, trait, row, column):
        actions = [
            Action(name="Configure", action=self.configure_name),
        ]
        mm = MenuManager(*actions)
        return mm

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        c = item.color
        if isinstance(c, (list, tuple)):
            c = [x * 255 for x in c]
        return c

    def get_text_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        color = "black"
        if isinstance(item.color, (list, tuple)):
            if sum(item.color[:3]) < 1.5:
                color = "white"
        return color


class GroupedPositionsAdapter(PositionsAdapter, ConfigurableMixin):
    columns = [
        ("Identifier", "identifier"),
        ("Irradiation", "irradiation_str"),
        ("Sample", "sample"),
        ("Material", "material"),
        ("Positions", "position_str"),
    ]

    all_columns = [
        ("Identifier", "identifier"),
        ("Packet", "packet"),
        ("Irradiation", "irradiation_str"),
        ("Sample", "sample"),
        ("Material", "material"),
        ("Positions", "position_str"),
    ]

    configure_name = "configure_grouped_position_table"
    # def get_menu(self, obj, trait, row, column):
    #     actions = [
    #         Action(name="Configure", action="configure_grouped_position_table"),
    #     ]
    #     mm = MenuManager(*actions)
    #     return mm


class BaseLoadPane(TraitsDockPane):
    display_load_name = Property(depends_on="model.load_name")

    # display_tray_name = Property(depends_on='model.tray')

    def _get_display_load_name(self):
        if self.model.load_instance:
            ret = '<font size=12 color="blue"><b>{} ({}) {}</b></font>'.format(
                self.model.load_instance.name,
                self.model.tray,
                self.model.load_instance.create_date,
            )
        else:
            ret = ""
        return ret


class PositionTableConfigurer(TableConfigurer):
    id = "position_table"

    def traits_view(self):
        v = VGroup(
            UItem(
                "columns",
                style="custom",
                editor=CheckListEditor(name="available_columns", cols=3),
            ),
            Item("font", enabled_when="fontsize_enabled"),
        )
        return okcancel_view(
            v,
            # kind='modal',
            title="Configure Position Table",
            handler=TableConfigurerHandler(),
        )


class GroupedPositionTableConfigurer(TableConfigurer):
    id = "grouped_position_table"

    def traits_view(self):
        v = VGroup(
            UItem(
                "columns",
                style="custom",
                editor=CheckListEditor(name="available_columns", cols=3),
            ),
            Item("font", enabled_when="fontsize_enabled"),
        )
        return okcancel_view(
            v,
            # kind='modal',
            title="Configure Grouped Position Table",
            handler=TableConfigurerHandler(),
        )


class LoadTableHandler(Handler):
    def configure_position_table(self, info, obj):
        pane = info.ui.context["pane"]
        tb = pane.position_configurer
        tb.edit_traits()

    def configure_grouped_position_table(self, info, obj):
        pane = info.ui.context["pane"]
        tb = pane.grouped_position_configurer
        tb.edit_traits()


class LoadTablePane(BaseLoadPane):
    name = "Positions"
    id = "pychron.loading.positions"

    position_configurer = Instance(PositionTableConfigurer)
    grouped_position_configurer = Instance(GroupedPositionTableConfigurer)

    position_adapter = Instance(PositionsAdapter)
    grouped_position_adapter = Instance(GroupedPositionsAdapter)

    def __init__(self, *args, **kw):
        super(LoadTablePane, self).__init__(*args, **kw)
        self.position_configurer.load()
        self.grouped_position_configurer.load()

    def _position_configurer_default(self):
        c = PositionTableConfigurer()
        c.set_adapter(self.position_adapter)
        return c

    def _grouped_position_configurer_default(self):
        c = GroupedPositionTableConfigurer()
        c.set_adapter(self.grouped_position_adapter)
        return c

    def _position_adapter_default(self):
        return PositionsAdapter()

    def _grouped_position_adapter_default(self):
        return GroupedPositionsAdapter()

    def traits_view(self):
        a = HGroup(spring, UItem("pane.display_load_name", style="readonly"), spring)

        b = UItem(
            "positions",
            editor=TabularEditor(adapter=self.position_adapter,
                                 refresh="refresh_table",
                                 multi_select=True),
        )
        c = UItem(
            "grouped_positions",
            label="Grouped Positions",
            editor=TabularEditor(adapter=self.grouped_position_adapter,
                                 refresh="refresh_table"),
        )

        v = View(VGroup(spring, a, Tabbed(b, c)), handler=LoadTableHandler())
        return v


class LoadInstanceAdapter(TabularAdapter):
    columns = [("Load", "name"), ("Create Date", "create_date"),
               ("Tray", "tray")]
    font = "modern 10"


class LoadPane(TraitsTaskPane):
    def traits_view(self):
        v = View(Tabbed(VGroup(UItem("canvas", style="custom", editor=ComponentEditor()), label='Canvas'),
                        VGroup(UItem("mv_canvas", style="custom", editor=ComponentEditor()), label='MV')))
        return v


class MachineVisionPane(TraitsDockPane):
    name = "Machine Vision"
    id = "pychron.loading.machine_vision"

    def traits_view(self):
        v = View(VGroup(UItem('object.autocenter_manager.pxpermm'),
                        UItem(
                            "object.autocenter_manager.display_image",
                            width=-400,
                            height=-400,
                            editor=ImageEditor(
                                refresh="object.autocenter_manager."
                                        "display_image.refresh_needed"
                            )),
                        ))
        return v


class VideoPane(TraitsDockPane):
    name = "Video"
    id = "pychron.loading.video"

    # def trait_context(self):
    #     return {'object': self.model.stage_manager}

    def traits_view(self):
        # v = View(VGroup(UItem("video",
        #                       width=320,
        #                       height=240,
        #                       resizable=True,
        #                       style="custom", editor=VideoEditor())),
        #          )
        editor = self.model.canvas_editor_factory()
        return View(UItem("canvas", style="custom", editor=editor))


class StageManagerPane(TraitsDockPane):
    name = "Stage"
    id = "pychron.loading.stage"

    def trait_context(self):
        sm = self.model.stage_manager
        return {
            "stage_manager": sm,
            "tray_calibration": sm.tray_calibration_manager,
            "object": sm,
            "foot_pedal": self.model.foot_pedal,
            "focus_motor": self.model.focus_motor,
            "loading_manager": self.model
        }

    def calibration_view(self):
        cal_help_grp = VGroup(
            CustomLabel("tray_calibration.calibration_help", color="green"),
            label="Help",
            show_border=True,
        )

        cal_results_grp = VGroup(
            HGroup(
                rfloatitem("tray_calibration.cx"), rfloatitem("tray_calibration.cy")
            ),
            rfloatitem("tray_calibration.rotation"),
            rfloatitem("tray_calibration.scale", sigfigs=4),
            rfloatitem("tray_calibration.error", sigfigs=2),
            label="Results",
            show_border=True,
        )

        # holes_grp = VGroup(HGroup(UItem('tray_calibration.add_holes_button',
        #                                 tooltip='Add Holes'),
        #                           UItem('tray_calibration.reset_holes_button',
        #                                 tooltip='Reset Holes')),
        #                    UItem('tray_calibration.holes_list',
        #                          editor=ListStrEditor()))

        cal_grp = HGroup(
            UItem(
                "tray_calibration.style",
                enabled_when="not tray_calibration.isCalibrating()",
            ),
            UItem(
                "stage_manager.stage_map_name",
                editor=EnumEditor(name="stage_manager.stage_map_names"),
            ),
            UItem(
                "tray_calibration.calibrate",
                enabled_when="tray_calibration.calibration_enabled",
                editor=ButtonEditor(
                    label_value="tray_calibration.calibration_step"
                ),
                width=-125,
            ),
            UItem(
                "tray_calibration.cancel_button",
                enabled_when="tray_calibration.isCalibrating()",
            ),
            UItem("tray_calibration.set_center_button"),
            UItem("tray_calibration.clear_corrections_button")
        )
        tc_grp = VGroup(
            cal_grp,
            UItem("tray_calibration.calibrator", style="custom"),
            HGroup(cal_results_grp, cal_help_grp),
            label="Calibration",
        )
        return tc_grp

    def counter_view(self):
        g = BorderHGroup(Item('foot_pedal.max_count'),
                         CustomLabel('foot_pedal.count',
                                     size=20,
                                     color='orange',
                                     bgcolor='black',
                                     use_color_background=True,
                                     style='readonly'),
                         label="Foot Pedal"
                         )
        return g

    def traits_view(self):
        v = View(
            VGroup(HGroup(UItem("calibrated_position_entry",
                                tooltip="Enter a position e.g 1 for a hole, " "or 3,4 for X,Y"),
                          icon_button_editor('autocenter_button', "find")
                          ),
                   UItem('stage_controller', style='custom'),
                   HGroup(Item('loading_manager.loading_level_button'),
                          Item('loading_manager.checking_level_button')),
                   HGroup(Item('loading_manager.up_button'),
                          Item('loading_manager.down_button')),
                   HGroup(UItem('home'),
                          icon_button_editor("snapshot_button", "camera"), spring),
                   self.calibration_view(),
                   self.counter_view()
                   )

        )
        return v


class LoadDockPane(BaseLoadPane):
    name = "Load"
    id = "pychron.loading.load"

    def traits_view(self):
        a = HGroup(
            Item("pane.display_load_name", style="readonly", label="Load"), spring
        )
        b = UItem("canvas", style="custom", editor=ComponentEditor())
        v = View(VGroup(a, b))

        return v


class LoadControlPane(TraitsDockPane):
    name = "Load Editor"
    id = "pychron.loading.controls"

    def traits_view(self):
        notegrp = VGroup(
            Item(
                "retain_note", tooltip="Retain the Note for the next hole", label="Lock"
            ),
            Item("note", style="custom", show_label=False),
            show_border=True,
            label="Note",
        )

        viewgrp = VGroup(
            HGroup(
                Item("use_cmap", label="Color Map"),
                UItem("cmap_name", enabled_when="use_cmap"),
            ),
            HGroup(
                Item("show_hole_numbers"), Item("show_identifiers", label="Identifiers")
            ),
            HGroup(Item("show_weights"), Item("show_nxtals", label="N. Xtals")),
            Item("show_samples"),
            # Item('show_spans'),
            show_border=True,
            label="View",
        )

        load_grp = VGroup(
            HGroup(
                Item(
                    "username",
                    label="User",
                    editor=EnumEditor(name="available_user_names"),
                ),
                icon_button_editor("add_button", "add", tooltip="Add a load"),
                icon_button_editor(
                    "delete_button", "delete", tooltip="Delete selected load"
                ),
                icon_button_editor(
                    "archive_button",
                    "application-x-archive",
                    tooltip="Archive a set of loads",
                ),
                icon_button_editor(
                    "unarchive_button",
                    "application-x-archive",
                    tooltip="Unarchive a set of loads",
                ),
            ),
            UItem(
                "loads",
                editor=FilterTabularEditor(
                    adapter=LoadInstanceAdapter(),
                    use_fuzzy=True,
                    editable=False,
                    multi_select=True,
                    selected="selected_instances",
                    stretch_last_section=False,
                ),
                height=250,
            ),
            label="Load",
            show_border=True,
        )

        samplegrp = VGroup(
            HGroup(
                UItem("irradiation", editor=EnumEditor(name="irradiations")),
                UItem("level", editor=EnumEditor(name="levels")),
                UItem("identifier", editor=EnumEditor(name="identifiers")),
            ),
            Item("sample_info", style="readonly"),
            Item("packet", style="readonly"),
            HGroup(
                Item("weight", label="Weight (mg)", springy=True),
                Item(
                    "retain_weight",
                    label="Lock",
                    tooltip="Retain the Weight for the next hole",
                ),
            ),
            HGroup(
                Item("nxtals", label="N. Xtals", springy=True),
                Item(
                    "retain_nxtals",
                    label="Lock",
                    tooltip="Retain the N. Xtals for the next hole",
                ),
            ),
            HGroup(
                Item("npositions", label="NPositions", springy=True),
                Item("auto_increment"),
            ),
            enabled_when="load_name",
            show_border=True,
            label="Sample",
        )

        v = View(VFold(load_grp, samplegrp, notegrp, viewgrp))
        return v

# ============= EOF =============================================
