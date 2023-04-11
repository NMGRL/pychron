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
from pyface.action.menu_manager import MenuManager
from traits.api import Int, Property, Str, Color, Bool, Event
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.core.helpers.color_generators import colornames
from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.resources import icon
from pychron.pychron_constants import (
    PLUSMINUS_ONE_SIGMA,
    PRECLEANUP,
    POSTCLEANUP,
    CLEANUP,
    EXTRACT_VALUE,
    DURATION,
    CRYO_TEMP,
)


class BrowserAdapter(TabularAdapter, ConfigurableMixin):
    font = "arial 10"
    name_width = Int(200)

    def get_tooltip(self, obj, trait, row, column):
        name = self.column_map[column]
        return "{}= {}".format(name, getattr(self.item, name))


class ProjectAdapter(BrowserAdapter):
    columns = [("Name", "name"), ("IR", "unique_id")]
    unique_id_width = Int(75)

    def get_menu(self, obj, trait, row, column):
        return MenuManager(Action(name="Unselect", action="unselect_projects"))


class PrincipalInvestigatorAdapter(BrowserAdapter):
    columns = [("Name", "name")]
    # name_width = Int(10)


class LoadAdapter(BrowserAdapter):
    columns = [("Name", "name")]


class SampleAdapter(BrowserAdapter):
    columns = [
        ("Sample", "name"),
        ("Material", "material"),
        ("Grainsize", "grainsize"),
        ("Project", "project"),
    ]

    all_columns = [
        ("Sample", "name"),
        ("Material", "material"),
        ("Grainsize", "grainsize"),
        ("Project", "project"),
        ("Note", "note"),
    ]
    #     material_text = Property
    odd_bg_color = "lightgray"

    name_width = Int(125)
    labnumber_width = Int(60)
    material_width = Int(75)

    def get_menu(self, obj, trait, row, column):
        return MenuManager(
            Action(
                name="Find Associated Identifiers", action="find_associated_identifiers"
            ),
            Action(name="Configure", action="configure_sample_table"),
        )


class SampleImageAdapter(BrowserAdapter):
    columns = [
        ("Sample", "name"),
        ("Identifier", "identifier"),
        ("Material", "material"),
        ("Project", "project"),
    ]


class LabnumberAdapter(BrowserAdapter):
    columns = [
        ("Sample", "name"),
        ("Identifier", "labnumber"),
        ("Material", "material"),
    ]
    all_columns = [
        ("Sample", "name"),
        ("Identifier", "labnumber"),
        ("Material", "material"),
        ("Project", "project"),
        ("Irradiation", "irradiation"),
        ("Level", "irradiation_and_level"),
        ("Irrad. Pos.", "irradiation_pos"),
        ("Packet", "packet"),
    ]
    odd_bg_color = "lightgray"

    name_width = Int(125)
    labnumber_width = Int(90)
    material_width = Int(75)

    def get_menu(self, obj, trait, row, column):
        if obj.selected_samples:
            return MenuManager(
                Action(name="Unselect", action="unselect_samples"),
                Action(name="Chronological View", action="load_chrono_view"),
                Action(name="Configure", action="configure_sample_table"),
            )


REVIEW_STATUS_ICONS = {
    "Default": icon("gray_ball"),
    "Intermediate": icon("orange_ball"),
    "All": icon("green_ball"),
}


class AnalysisAdapter(BrowserAdapter):
    all_columns = [
        ("Review", "review_status"),
        ("Run ID", "record_id"),
        ("UUID", "uuid"),
        ("Sample", "sample"),
        ("Material", "material"),
        ("Project", "project"),
        ("Repository", "repository_identifier"),
        ("Packet", "packet"),
        ("Irradiation", "irradiation_info"),
        ("Tag", "tag"),
        ("RunDate", "rundate"),
        ("Dt", "delta_time"),
        ("Spec.", "mass_spectrometer"),
        ("Meas.", "meas_script_name"),
        ("Ext.", "extract_script_name"),
        ("EVal.", EXTRACT_VALUE),
        ("Cleanup", CLEANUP),
        ("Pre Cleanup", PRECLEANUP),
        ("Post Cleanup", POSTCLEANUP),
        ("Cryo Temp", CRYO_TEMP),
        ("Dur", DURATION),
        ("Position", "position"),
        ("Device", "extract_device"),
        ("Load Name", "load_name"),
        ("Comment", "comment"),
    ]

    columns = [("Run ID", "record_id"), ("Tag", "tag"), ("Dt", "delta_time")]

    column_widths = Event

    review_status_width = Int(50)
    record_id_width = Int(70)
    uuid_width = Int
    sample_width = Int
    project_width = Int
    repository_identifier_width = Int
    packet_width = Int
    irradiation_info_width = Int
    tag_width = Int(60)
    rundate_width = Int(125)
    delta_time_width = Int(65)
    mass_spectrometer_width = Int
    meas_script_name_width = Int
    extract_script_name_width = Int
    extract_value_width = Int
    cleanup_width = Int
    pre_cleanup_width = Int
    post_cleanup_width = Int
    cryo_temperature_width = Int
    duration_width = Int
    position_width = Int
    extract_device_width = Int
    comment_width = Int
    load_name_width = Int
    material_width = Int

    review_status_image = Property
    review_status_text = Str("")
    delta_time_text = Property
    odd_bg_color = "lightgray"
    font = "arial 10"

    use_analysis_colors = Bool

    def run_history_columns(self):
        self.columns = [
            ("Run ID", "record_id"),
            ("Sample", "sample"),
            ("Project", "project"),
            ("Tag", "tag"),
            ("RunDate", "rundate"),
            ("Comment", "comment"),
            ("Position", "position"),
            ("EVal.", "extract_value"),
            ("Cleanup", "cleanup"),
            ("Dur", "duration"),
            ("Device", "extract_device"),
            ("Spec.", "mass_spectrometer"),
            ("Meas.", "meas_script_name"),
            ("Ext.", "extract_script_name"),
        ]

    def _get_review_status_image(self):
        s = self.item.review_status
        return REVIEW_STATUS_ICONS.get(s)

    def _get_delta_time_text(self):
        dt = self.item.delta_time
        if dt > 60:
            units = "(h)"
            dt /= 60.0
            if dt > 24:
                units = "(d)"
                dt /= 24.0
        else:
            units = ""
        return "{:0.1f} {}".format(dt, units)

    def get_menu(self, obj, trait, row, column):
        tag_actions = [
            Action(name="OK", action="tag_ok"),
            Action(name="Omit", action="tag_omit"),
            Action(name="Invalid", action="tag_invalid"),
            Action(name="Skip", action="tag_skip"),
        ]

        group_actions = [
            Action(name="Group Selected", action="group_selected"),
            Action(name="Clear Grouping", action="clear_grouping"),
        ]

        select_actions = [
            Action(name="Same Identifier", action="select_same"),
            Action(name="Same Attr", action="select_same_attr"),
            Action(name="Clear", action="clear_selection"),
            Action(name="Remove Others", action="remove_others"),
        ]

        actions = [
            Action(name="Configure", action="configure_analysis_table"),
            Action(name="Unselect", action="unselect_analyses"),
            Action(name="Open", action="recall_items"),
            Action(name="Review Status Details", action="review_status_details"),
            Action(name="Load Review Status", action="load_review_status"),
            Action(name="Toggle Freeze", action="toggle_freeze"),
            MenuManager(name="Selection", *select_actions),
            MenuManager(name="Grouping", *group_actions),
            MenuManager(name="Tag", *tag_actions),
        ]

        return MenuManager(*actions)

    def get_bg_color(self, obj, trait, row, column=0):
        color = "white"
        item = getattr(obj, trait)[row]
        if item.frozen:
            color = "#11BAF2"
        else:
            if item.delta_time > 1440:  # 24 hours
                color = "#FAE900"
            else:
                if row % 2:
                    color = "lightgray"
                if item.group_id >= 1:
                    gid = item.group_id % len(colornames)
                    color = colornames[gid]

                else:
                    if self.use_analysis_colors:
                        key = "{}_color".format(item.analysis_type)
                        if hasattr(self, key):
                            color = getattr(self, key)
                        else:
                            if item.analysis_type.startswith("blank"):
                                color = self.blank_color

        return color


class InterpretedAgeAdapter(TabularAdapter):
    columns = [
        ("Identifier", "identifier"),
        ("Name", "name"),
        ("Age", "age"),
        (PLUSMINUS_ONE_SIGMA, "age_err"),
        ("AgeKind", "age_kind"),
        ("AgeErrorKind", "age_error_kind"),
    ]

    font = "arial 10"

    age_text = Property
    age_err_text = Property

    def _get_age_text(self):
        return floatfmt(self.item.age, 3)

    def _get_age_err_text(self):
        return floatfmt(self.item.age_err, 3)

    def get_menu(self, obj, trait, row, column):
        actions = [
            Action(name="Delete", action="delete"),
        ]

        return MenuManager(*actions)


# ============= EOF =============================================
