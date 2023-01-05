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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Color, Instance, DelegatesTo, List, Any, Property, Button, Event
from traitsui.api import (
    View,
    Item,
    UItem,
    VGroup,
    HGroup,
    spring,
    Group,
    Spring,
    Label,
    VSplit,
    UReadonly,
    ListEditor,
    Readonly,
)
from traitsui.editors.api import TableEditor, EnumEditor
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.traitsui_shortcuts import VFold
from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.enum_editor import myEnumEditor
from pychron.core.ui.led_editor import LEDEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.plot_panel import PlotPanel
from pychron.experiment.utilities.identifier import SPECIAL_NAMES
from pychron.pychron_constants import (
    MEASUREMENT_COLOR,
    EXTRACTION_COLOR,
    NOT_EXECUTABLE_COLOR,
    SKIP_COLOR,
    SUCCESS_COLOR,
    CANCELED_COLOR,
    TRUNCATED_COLOR,
    FAILED_COLOR,
    END_AFTER_COLOR,
    SPECIAL_IDENTIFIER,
)


# ===============================================================================
# editing
# ===============================================================================


def spacer(w):
    return Spring(width=w, springy=False)


def queue_factory_name(name):
    return "object.queue_factory.{}".format(name)


def run_factory_name(name):
    return "object.run_factory.{}".format(name)


def queue_factory_item(name, **kw):
    return Item(queue_factory_name(name), **kw)


def queue_factory_uitem(name, **kw):
    kw["show_label"] = False
    return queue_factory_item(name, **kw)


def run_factory_item(name, **kw):
    return Item(run_factory_name(name), **kw)


def run_factory_uitem(name, **kw):
    kw["show_label"] = False
    return run_factory_item(name, **kw)


class ExperimentFactoryPane(TraitsDockPane):
    id = "pychron.experiment.factory"
    name = "Experiment Editor"
    info_label = Property(depends_on="model.run_factory.info_label")

    def _get_info_label(self):
        return '<font color="green"><b>{}</b></font>'.format(
            self.model.run_factory.info_label
        )

    def traits_view(self):
        add_button = icon_button_editor(
            "add_button",
            "add",
            # enabled_when='ok_add',
            tooltip="Add run",
        )

        save_button = icon_button_editor(
            "save_button", "disk", tooltip="Save queue to file"
        )

        edit_button = icon_button_editor(
            "edit_mode_button",
            "table_edit",
            enabled_when="edit_enabled",
            tooltip="Toggle edit mode",
        )

        clear_button = icon_button_editor(
            "clear_button",
            "table_row_delete",
            tooltip='Clear all runs added using "frequency"',
        )

        email_grp = BorderVGroup(
            HGroup(
                queue_factory_item(
                    "use_email", label="Use Email", tooltip="Send email notifications"
                ),
                queue_factory_item(
                    "use_group_email",
                    tooltip="Email a group of users",
                    label="Email Group",
                ),
                icon_button_editor(
                    queue_factory_name("edit_emails"), "cog", tooltip="Edit user group"
                ),
            ),
            queue_factory_uitem("email", springy=True),
            label="Email",
        )

        user_grp = BorderHGroup(
            UItem(
                queue_factory_name("username"),
                editor=ComboboxEditor(name=queue_factory_name("usernames")),
            ),
            icon_button_editor(queue_factory_name("edit_user"), "database_edit"),
            label="User",
        )

        load_select = BorderHGroup(
            queue_factory_uitem("load_name", width=150),
            queue_factory_item(
                "tray", editor=EnumEditor(name=queue_factory_name("trays"))
            ),
            icon_button_editor(
                queue_factory_name("select_existing_load_name_button"),
                "database_go",
                tooltip="Get Load from Database",
            ),
            label="Load",
        )

        generate_queue = BorderHGroup(
            icon_button_editor(
                "generate_queue_button",
                "brick-go",
                tooltip="Generate a experiment queue from the selected load",
                enabled_when="load_name",
            ),
            icon_button_editor(
                "edit_queue_config_button",
                "cog",
                tooltip="Configure experiment queue generation",
            ),
            label="Generate Queue",
        )

        lgrp = VGroup(load_select, generate_queue)

        ms_ed_grp = BorderVGroup(
            HGroup(
                queue_factory_uitem(
                    "mass_spectrometer",
                    editor=myEnumEditor(name=queue_factory_name("mass_spectrometers")),
                ),
                queue_factory_uitem(
                    "extract_device",
                    editor=myEnumEditor(name=queue_factory_name("extract_devices")),
                ),
            ),
            lgrp,
            queue_factory_item("default_lighting"),
            label="Spectrometer/Extract Device",
        )

        name = queue_factory_name("available_conditionals")
        queue_cond_grp = BorderHGroup(
            queue_factory_uitem(
                "queue_conditionals_name",
                label="Queue Conditionals",
                editor=myEnumEditor(name=name),
            ),
            label="Queue Conditionals",
        )

        delay_grp = BorderVGroup(
            queue_factory_item("delay_before_analyses", label="Before Analyses (s)"),
            queue_factory_item("delay_between_analyses", label="Between Analyses (s)"),
            queue_factory_item("delay_after_blank", label="After Blank (s)"),
            queue_factory_item("delay_after_air", label="After Air (s)"),
            label="Delays",
        )

        note_grp = BorderVGroup(
            queue_factory_uitem("note", style="custom", height=150), label="Note"
        )
        queue_grp = VGroup(
            user_grp,
            email_grp,
            ms_ed_grp,
            queue_cond_grp,
            delay_grp,
            note_grp,
            label="Queue",
        )

        button_bar = HGroup(
            save_button,
            add_button,
            clear_button,
            edit_button,
            CustomLabel(run_factory_name("edit_mode_label"), color="red", width=40),
            spring,
        )
        button_bar2 = HGroup(
            Item("auto_increment_id", label="Auto Increment Identifier"),
            Item(
                "auto_increment_id_count",
                width=-100,
                enabled_when="auto_increment_id",
                label="Increment",
            ),
            Item("auto_increment_position", label="Position"),
        )
        edit_grp = VFold(
            queue_grp,
            VGroup(
                self._get_info_group(),
                self._get_extract_group(),
                enabled_when=queue_factory_name("ok_make"),
                label="General",
            ),
            self._get_script_group(),
            self._get_truncate_group(),
        )

        v = View(
            VGroup(
                button_bar,
                button_bar2,
                UItem("pane.info_label", style="readonly"),
                edit_grp,
                enabled_when="edit_enabled",
            ),
            kind="live",
            width=225,
        )
        return v

    def _get_info_group(self):
        a = HGroup(
            run_factory_uitem(
                "selected_irradiation",
                editor=myEnumEditor(name=run_factory_name("irradiations")),
            ),
            run_factory_uitem(
                "selected_level", editor=myEnumEditor(name=run_factory_name("levels"))
            ),
            run_factory_item(
                "labnumber",
                tooltip="Enter a Identifier, aka L#",
                width=-200,
                label="Identifier",
                enabled_when='{} == "{}"'.format(
                    run_factory_name("special_labnumber"), SPECIAL_IDENTIFIER
                ),
                editor=myEnumEditor(name=run_factory_name("display_labnumbers")),
            ),
        )
        grp = BorderVGroup(
            a,
            HGroup(
                run_factory_uitem(
                    "special_labnumber", editor=myEnumEditor(values=SPECIAL_NAMES)
                ),
                run_factory_uitem(
                    "run_block",
                    editor=myEnumEditor(name=run_factory_name("run_blocks")),
                ),
                icon_button_editor(run_factory_name("edit_run_blocks"), "cog"),
                run_factory_item("frequency_model.frequency_int", width=50),
                icon_button_editor(run_factory_name("edit_frequency_button"), "cog"),
                spring,
            ),
            HGroup(
                run_factory_item("aliquot", width=50),
                run_factory_item(
                    "delay_after",
                    label="Delay After (s)",
                    tooltip="Time (s) to delay after this analysis. This value supersedes "
                    '"Delay Between Analyses" or "Delay After Blank"',
                ),
                spring,
            ),
            HGroup(
                run_factory_item(
                    "repository_identifier",
                    label="Repository ID",
                    editor=myEnumEditor(
                        name=run_factory_name("repository_identifiers")
                    ),
                ),
                icon_button_editor(
                    run_factory_name("add_repository_identifier"),
                    "add",
                    tooltip="Add a new repository",
                ),
                icon_button_editor(
                    run_factory_name("set_repository_identifier_button"),
                    "arrow_right",
                    tooltip="Set select runs repository_identifier to current value",
                ),
                icon_button_editor(
                    run_factory_name("clear_repository_identifier_button"), "clear"
                ),
                UItem(
                    run_factory_name("use_project_based_repository_identifier"),
                    tooltip="Use repository identifier based on project name",
                ),
            ),
            HGroup(
                run_factory_item(
                    "weight",
                    label="Weight (mg)",
                    tooltip="(Optional) Enter the weight of the sample in mg. "
                    "Will be saved in Database with analysis",
                ),
                run_factory_item(
                    "comment",
                    tooltip="(Optional) Enter a comment for this sample. "
                    "Will be saved in Database with analysis",
                ),
                run_factory_uitem(
                    "auto_fill_comment",
                    tooltip='Auto fill "Comment" with IrradiationLevel:Hole, e.g A:9',
                ),
                icon_button_editor(
                    run_factory_name("edit_comment_template"),
                    "cog",
                    tooltip="Edit comment template",
                ),
                icon_button_editor(
                    run_factory_name("apply_comment_button"),
                    "arrow_right",
                    tooltip="Apply comment template to rows",
                ),
            ),
            HGroup(
                run_factory_item("flux", format_str="%0.4E"),
                Label("\u00b1"),
                run_factory_uitem("flux_error", format_str="%0.4E"),
                icon_button_editor(
                    run_factory_name("save_flux_button"),
                    "database_save",
                    tooltip="Save flux to database",
                ),
                enabled_when=run_factory_name("labnumber"),
            ),
            label="Sample Info",
        )
        return grp

    def _get_truncate_group(self):
        grp = VGroup(
            HGroup(
                run_factory_item("use_simple_truncation", label="Use Simple"),
                icon_button_editor(
                    run_factory_name("clear_conditionals"),
                    "delete",
                    tooltip="Clear Conditionals from selected runs",
                ),
            ),
            BorderHGroup(
                run_factory_uitem(
                    "trunc_attr",
                    editor=myEnumEditor(name=run_factory_name("trunc_attrs")),
                ),
                run_factory_uitem("trunc_comp"),
                run_factory_uitem("trunc_crit"),
                spacer(-10),
                run_factory_item("trunc_start", label="Start Count"),
                label="Simple",
            ),
            BorderHGroup(
                run_factory_item(
                    "conditionals_path",
                    editor=myEnumEditor(name=run_factory_name("conditionals")),
                    label="Path",
                ),
                icon_button_editor(
                    run_factory_name("edit_conditionals_button"),
                    "table_edit",
                    # enabled_when=run_factory_name('conditionals_path_enabled'),
                    tooltip="Edit the selected conditionals file",
                ),
                icon_button_editor(
                    run_factory_name("new_conditionals_button"),
                    "table_add",
                    tooltip="Add a new conditionals file. Duplicated currently "
                    "selected file if applicable",
                ),
                icon_button_editor(
                    run_factory_name("apply_conditionals_button"),
                    "arrow_left",
                    tooltip="Apply conditionals file to selected analyses",
                ),
                label="File",
            ),
            enabled_when=queue_factory_name("ok_make"),
            label="Run Conditionals",
        )
        return grp

    def _get_script_group(self):
        script_grp = BorderVGroup(
            run_factory_uitem("extraction_script", style="custom"),
            run_factory_uitem("measurement_script", style="custom"),
            run_factory_uitem("post_equilibration_script", style="custom"),
            run_factory_uitem("post_measurement_script", style="custom"),
            run_factory_uitem("script_options", style="custom"),
            HGroup(
                spring,
                run_factory_uitem(
                    "default_fits_button",
                    enabled_when=run_factory_name("default_fits_enabled"),
                    label="Default Fits",
                ),
                run_factory_uitem(
                    "load_defaults_button",
                    tooltip="load the default scripts for this analysis type",
                    enabled_when=run_factory_name("labnumber"),
                ),
            ),
            enabled_when=queue_factory_name("ok_make"),
            label="Scripts",
        )
        return script_grp

    def _get_extract_group(self):
        return Group(run_factory_uitem("factory_view", style="custom"))


# ===============================================================================
# execution
# ===============================================================================
class ConnectionStatusPane(TraitsDockPane):
    id = "pychron.experiment.connection_status"
    name = "Connection Status"

    def traits_view(self):
        cols = [
            ObjectColumn(name="name", editable=False),
            ObjectColumn(name="connected", editable=False),
        ]
        v = View(
            UItem(
                "connectables",
                editor=TableEditor(editable=False, sortable=False, columns=cols),
            )
        )
        return v


class StatsPane(TraitsDockPane):
    id = "pychron.experiment.stats"
    name = "Stats"
    recalculate_button = Button("Recalculate")
    executor = Any

    def _recalculate_button_fired(self):
        self.model.experiment_queues = self.executor.experiment_queues
        self.model.reset()

    def traits_view(self):
        gen_grp = BorderVGroup(
            HGroup(UItem("pane.recalculate_button")),
            HGroup(
                Readonly("nruns", width=150, label="Total Runs"),
                UReadonly("total_time"),
            ),
            HGroup(
                Readonly("nruns_finished", width=150, label="Completed"),
                UReadonly("elapsed"),
            ),
            Readonly("remaining", label="Remaining"),
            Readonly("etf", label="Est. finish"),
            label="General",
        )
        cur_grp = BorderVGroup(
            Readonly(
                "current_run_duration",
            ),
            Readonly("run_elapsed"),
            label="Current",
        )
        sel_grp = BorderVGroup(
            Readonly("start_at"),
            Readonly("end_at"),
            Readonly("run_duration"),
            label="Selection",
        )
        v = View(VGroup(gen_grp, cur_grp, sel_grp))
        return v


class ConditionalsPane(TraitsDockPane):
    id = "pychron.experiment.conditionals"
    name = "Conditionals"

    def traits_view(self):
        return View(UItem("conditionals_view", style="custom"))


class ControlsPane(TraitsDockPane):
    # name = 'Controls'
    id = "pychron.experiment.controls"

    movable = False
    closable = False
    floatable = False

    start_button = Event
    stop_button = Event
    configure_scheduled_button = Event
    abort_run_button = Button("Abort Run")
    truncate_button = Button("Truncate Run")
    show_conditionals_button = Button("Show Conditionals")

    def _start_button_fired(self):
        self.task.execute()

    def _stop_button_fired(self):
        self.model.stop_run()

    def _abort_run_button_fired(self):
        self.model.abort_run()

    def _truncate_button_fired(self):
        if self.model.measuring_run:
            self.model.measuring_run.truncate_run(self.truncate_style)

    def _show_conditionals_button_fired(self):
        self.model.show_conditionals(main_thread=False)

    def _configure_scheduled_button_fired(self):
        self.model.scheduler.setup()
        self.model.scheduler.edit_traits(kind="livemodal")

    def traits_view(self):
        cancel_tt = """Cancel current run and continue to next run"""
        stop_tt = """Cancel current run and stop queue"""
        start_tt = """Start current experiment queue. 
Will continue to next opened queue when completed"""
        truncate_tt = """Stop the current measurement process and continue to 
the next step in the measurement script"""
        truncate_style_tt = """Normal= measure_iteration stopped at current step
    script continues
Quick=   measure_iteration stopped at current step
    script continues using abbreviated_count_ratio*counts"""
        end_tt = """Stop the queue and the end of the current run"""

        schedule_tt = """Set a scheduled start time"""

        v = View(
            HGroup(
                UItem("alive", editor=LEDEditor(colors=["red", "green"], radius=30)),
                spacer(-20),
                icon_button_editor(
                    "pane.start_button",
                    "start",
                    enabled_when="can_start",
                    tooltip=start_tt,
                ),
                icon_button_editor(
                    "pane.configure_scheduled_button",
                    "calendar",
                    enabled_when="can_start",
                    tooltip=schedule_tt,
                ),
                icon_button_editor(
                    "pane.stop_button",
                    "stop",
                    enabled_when="not can_start",
                    tooltip=stop_tt,
                ),
                spacer(-20),
                Item(
                    "end_at_run_completion", label="Stop at Completion", tooltip=end_tt
                ),
                spacer(-20),
                icon_button_editor(
                    "pane.abort_run_button",
                    "cancel",
                    # enabled_when='can_cancel',
                    tooltip=cancel_tt,
                ),
                spacer(-20),
                icon_button_editor(
                    "pane.truncate_button",
                    "lightning",
                    enabled_when="measuring",
                    tooltip=truncate_tt,
                ),
                UItem(
                    "truncate_style",
                    enabled_when="measuring",
                    tooltip=truncate_style_tt,
                ),
                UItem("pane.show_conditionals_button"),
                spacer(-75),
                CustomLabel(
                    "object.experiment_status.label",
                    color_name="object.experiment_status.color",
                    size=24,
                    weight="bold",
                ),
                spring,
            )
        )
        return v


class ExplanationPane(TraitsDockPane):
    id = "pychron.experiment.explanation"
    name = "Explanation"
    measurement = Color(MEASUREMENT_COLOR)
    extraction = Color(EXTRACTION_COLOR)
    success = Color(SUCCESS_COLOR)
    skip = Color(SKIP_COLOR)
    canceled = Color(CANCELED_COLOR)
    truncated = Color(TRUNCATED_COLOR)
    failed = Color(FAILED_COLOR)
    not_executable = Color(NOT_EXECUTABLE_COLOR)
    end_after = Color(END_AFTER_COLOR)

    def set_colors(self, cd):
        for k, v in cd.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(
                    Label("Extraction"),
                    spring,
                    UReadonly(
                        "extraction",
                    ),
                ),
                HGroup(
                    Label("Measurement"),
                    spring,
                    UReadonly(
                        "measurement",
                    ),
                ),
                HGroup(
                    Label("Skip"),
                    spring,
                    UReadonly(
                        "skip",
                    ),
                ),
                HGroup(
                    Label("Success"),
                    spring,
                    UReadonly(
                        "success",
                    ),
                ),
                HGroup(
                    Label("Truncated"),
                    spring,
                    UReadonly(
                        "truncated",
                    ),
                ),
                HGroup(
                    Label("Canceled"),
                    spring,
                    UReadonly(
                        "canceled",
                    ),
                ),
                HGroup(
                    Label("Failed"),
                    spring,
                    UReadonly(
                        "failed",
                    ),
                ),
                HGroup(
                    Label("Not Executable"),
                    spring,
                    UReadonly(
                        "not_executable",
                    ),
                ),
                HGroup(
                    Label("End After"),
                    spring,
                    UReadonly(
                        "end_after",
                    ),
                ),
            )
        )
        return v


class IsotopeEvolutionPane(TraitsDockPane):
    id = "pychron.experiment.isotope_evolution"
    name = "Isotope Evolutions"
    plot_panel = Instance(PlotPanel, ())
    is_peak_hop = DelegatesTo("plot_panel")
    continue_button = Button

    def _continue_button_fired(self):
        self.plot_panel.ncounts = 0

    def traits_view(self):
        v = View(
            VSplit(
                UItem("object.plot_panel.graph_container", style="custom", height=0.75),
                VGroup(
                    HGroup(
                        Spring(springy=False, width=-5),
                        Item(
                            "object.plot_panel.ncycles",
                            label="Cycles",
                            tooltip="Set the number of measurement cycles",
                            visible_when="is_peak_hop",
                            width=-50,
                        ),
                        Spring(springy=False, width=-10),
                        CustomLabel(
                            "object.plot_panel.current_cycle",
                            color="blue",
                            color_name="object.plot_panel.current_color",
                            # width=2,
                            visible_when="is_peak_hop",
                        ),
                        Spring(springy=False, width=-10),
                        Item(
                            "object.plot_panel.ncounts",
                            label="Counts",
                            tooltip="Set the number of measurement points",
                        ),
                        icon_button_editor(
                            "continue_button",
                            "arrow-right-double-2",
                            tooltip="Continue to next measurement step. "
                            'Simply sets "Counts" to 0',
                        ),
                        Spring(springy=False, width=-10),
                        CustomLabel(
                            "object.plot_panel.display_counts",
                            color="red",
                            size=14,
                            width=50,
                        ),
                        Spring(springy=False, width=-5),
                    ),
                    UItem(
                        "object.plot_panel.analysis_view", style="custom", height=0.25
                    ),
                ),
            )
        )
        return v


class LoggerPane(TraitsDockPane):
    loggers = List
    selected = Any
    name = "Logger"
    id = "pychron.experiment.logger"

    def __init__(self, *args, **kw):
        super(LoggerPane, self).__init__(*args, **kw)
        from pychron.core.displays.gdisplays import gWarningDisplay, gLoggerDisplay

        self.loggers = [gLoggerDisplay, gWarningDisplay]

    def traits_view(self):
        v = View(
            UItem(
                "loggers",
                editor=ListEditor(
                    use_notebook=True, page_name=".title", selected="selected"
                ),
                style="custom",
            )
        )

        return v


# ============= EOF =============================================
