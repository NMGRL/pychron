# ===============================================================================
# Copyright 2011 Jake Ross
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

# ============= enthought library imports=======================
from pyface.action.menu_manager import MenuManager
from traits.api import Property, Int, Dict, Bool
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.envisage.resources import icon
from pychron.experiment.utilities.runid import make_aliquot_step
from pychron.pychron_constants import (
    EXTRACTION_COLOR,
    MEASUREMENT_COLOR,
    SUCCESS_COLOR,
    SKIP_COLOR,
    NOT_EXECUTABLE_COLOR,
    CANCELED_COLOR,
    TRUNCATED_COLOR,
    FAILED_COLOR,
    END_AFTER_COLOR,
    BLANK_UNKNOWN,
    DEGAS,
    UNKNOWN,
    PRECLEANUP,
    WEIGHT,
    POSTCLEANUP,
    CLEANUP,
    DURATION,
    BEAM_DIAMETER,
    EXTRACT_VALUE,
    RAMP_DURATION,
    EXTRACT_UNITS,
    POSITION,
    REPOSITORY_IDENTIFIER,
    MATERIAL,
    PROJECT,
    SAMPLE,
    OVERLAP,
    PATTERN,
    USE_CDD_WARMING,
    DELAY_AFTER,
    COMMENT,
    CRYO_TEMP,
    FAILED,
    CANCELED,
    TRUNCATED,
    SUCCESS,
    EXTRACTION,
    MEASUREMENT,
    INVALID,
    END_AFTER,
    ABORTED, MASS_SPECTROMETER,
)

# ============= local library imports  ==========================
COLORS = {
    SUCCESS: SUCCESS_COLOR,
    EXTRACTION: EXTRACTION_COLOR,
    MEASUREMENT: MEASUREMENT_COLOR,
    CANCELED: CANCELED_COLOR,
    TRUNCATED: TRUNCATED_COLOR,
    FAILED: FAILED_COLOR,
    END_AFTER: END_AFTER_COLOR,
    INVALID: "red",
    ABORTED: "orange",
}

GRAY_BALL = icon("gray_ball")
GREEN_BALL = icon("green_ball")
ORANGE_BALL = icon("orange_ball")

jump = MenuManager(
    Action(name="Jump to Start", action="jump_to_start"),
    Action(name="Jump to End", action="jump_to_end"),
    name="Jump",
)

move = MenuManager(
    Action(name="Move to Start", action="move_to_start"),
    Action(name="Move to End", action="move_to_end"),
    Action(name="Move Up", action="move_up"),
    Action(name="Move Down", action="move_down"),
    Action(name="Move to ...", action="move_to_row"),
    name="Move",
)

copy = MenuManager(
    Action(name="Copy to Start", action="copy_to_start"),
    Action(name="Copy to End", action="copy_to_end"),
    name="Copy",
)

blocks = MenuManager(
    Action(name="Make Block", action="make_block"),
    Action(name="Repeat Block", action="repeat_block"),
    name="Blocks",
)

selects = MenuManager(
    Action(name="Select Unknowns", action="select_unknowns"),
    Action(name="Select Special", action="select_special"),
    Action(name="Select Same Identifier", action="select_same"),
    Action(name="Select Same Attributes...", action="select_same_attr"),
    name="Select",
)

group_e = MenuManager(
    Action(name="AAA,BBB,CCC", action="group_extractions"),
    Action(name="ABC,ABC,ABC", action="group_extractions2"),
    name="Group Extractions",
)

randomize = MenuManager(
    Action(name="Randomize Unknowns", action="randomize_unknowns"),
    Action(name="Randomize All", action="randomize_all"),
    Action(name="Order From File", action="order_from_file"),
    Action(name="Motion Saver", action="motion_saver"),
    name="Position Ordering",
)

EDIT_MENU = MenuManager(
    move,
    copy,
    jump,
    blocks,
    selects,
    group_e,
    randomize,
    Action(name="Value Editor", action="open_value_editor"),
    Action(name="Configure", action="configure_table"),
    Action(name="Unselect", action="unselect"),
    Action(name="Toggle End After", action="toggle_end_after"),
    Action(name="Toggle Skip", action="toggle_skip"),
)


class ExecutedAutomatedRunSpecAdapter(TabularAdapter, ConfigurableMixin):
    all_columns = [
        ("-", "result_str"),
        ("Identifier", "labnumber"),
        ("Aliquot", "aliquot"),
        ("Sample", SAMPLE),
        ("Project", PROJECT),
        ("Irradiation", "irradiation"),
        ("Irrad. Level", "irradiation_level"),
        ("Irrad. Position", "irradiation_position"),
        ("Material", MATERIAL),
        ("RepositoryID", REPOSITORY_IDENTIFIER),
        ("Position", POSITION),
        ("Extract", EXTRACT_VALUE),
        ("Units", EXTRACT_UNITS),
        ("Ramp (s)", RAMP_DURATION),
        ("Duration (s)", DURATION),
        ("Cleanup (s)", CLEANUP),
        ("Pre Cleanup (s)", PRECLEANUP),
        ("Post Cleanup (s)", POSTCLEANUP),
        ("Cryo Temp. (K)", CRYO_TEMP),
        ("Overlap (s)", OVERLAP),
        ("Beam (mm)", BEAM_DIAMETER),
        ("Pattern", PATTERN),
        ("Extraction", "extraction_script"),
        ("T_o Offset", "collection_time_zero_offset"),
        ("Measurement", "measurement_script"),
        ("Conditionals", "conditionals"),
        ("SynExtraction", "syn_extraction_script"),
        ("CDDWarm", USE_CDD_WARMING),
        ("Post Eq.", "post_equilibration_script"),
        ("Post Meas.", "post_measurement_script"),
        ("Options", "script_options"),
        ("Comment", COMMENT),
        ("Weight", WEIGHT),
        ("Delay After", DELAY_AFTER),
        ("Mass Spec.", MASS_SPECTROMETER),
    ]

    columns = [
        ("Identifier", "labnumber"),
        ("Aliquot", "aliquot"),
    ]
    font = "arial 10"
    # all_columns = List
    # all_columns_dict = Dict
    # ===========================================================================
    # widths
    # ===========================================================================
    result_str_image = Property

    result_str_width = Int(25)
    repository_identifier_width = Int(90)
    labnumber_width = Int(80)
    aliquot_width = Int(60)
    sample_width = Int(50)
    position_width = Int(50)
    extract_value_width = Int(50)
    extract_units_width = Int(40)
    duration_width = Int(70)
    ramp_duration_width = Int(50)
    cleanup_width = Int(70)
    pre_cleanup_width = Int(70)
    post_cleanup_width = Int(70)
    cryo_temperature_width = Int(70)

    pattern_width = Int(80)
    beam_diameter_width = Int(65)

    overlap_width = Int(50)
    # autocenter_width = Int(70)
    #    extract_device_width = Int(125)
    extraction_script_width = Int(80)
    measurement_script_width = Int(90)
    conditionals_width = Int(80)
    syn_extraction_width = Int(80)
    use_cdd_warming_width = Int(80)
    post_measurement_script_width = Int(90)
    post_equilibration_script_width = Int(90)

    position_text = Property
    comment_width = Int(125)
    # ===========================================================================
    # number values
    # ===========================================================================
    ramp_duration_text = Property
    extract_value_text = Property
    beam_diameter_text = Property
    duration_text = Property
    cleanup_text = Property
    pre_cleanup_text = Property
    post_cleanup_text = Property
    cryo_temperature_text = Property

    aliquot_text = Property
    overlap_text = Property
    weight_text = Property

    # ===========================================================================
    # non cell editable
    # ===========================================================================
    # result_text = Property
    use_cdd_warming_text = Property
    colors = Dict(COLORS)

    use_analysis_type_colors = Bool
    analysis_type_colors = Dict

    AutomatedRunSpec_tooltip = Property
    AutomatedRunSpec_bg_color = Property
    AutomatedRunSpec_menu = Property

    def get_row_label(self, section, obj=None):
        return section + 1

    def _get_AutomatedRunSpec_tooltip(self):
        name = self.column_id
        item = self.item
        if name == "result_str":
            if item.state in ("success", "truncated"):
                return item.result.summary
        else:
            return "{}= {}\nstate= {}".format(name, getattr(item, name), item.state)

    def _get_AutomatedRunSpec_bg_color(self):
        item = self.item
        if not item.executable:
            color = NOT_EXECUTABLE_COLOR
        else:
            color = None
            if item.skip:
                color = SKIP_COLOR  # '#33CCFF'  # light blue
            elif item.state in self.colors:
                color = self.colors[item.state]
            elif item.end_after:
                color = END_AFTER_COLOR
            elif self.use_analysis_type_colors:
                atype = item.analysis_type
                if atype.startswith("blank"):
                    atype = "blank"
                color = self.analysis_type_colors.get(atype)

            if color is None:
                if self.row % 2 == 0:
                    color = self.even_bg_color
                else:
                    color = self.odd_bg_color  # '#E6F2FF'  # light gray blue

        return color

    def _get_AutomatedRunSpec_menu(self):
        item = self.item
        if item.state in ("success", "truncated"):
            evo_actions = [
                Action(name="Show All", action="show_evolutions"),
                Action(name="Show All w/Equilibration", action="show_evolutions_w_eq"),
                Action(
                    name="Show All w/Equilibration+Baseline",
                    action="show_evolutions_w_eq_bs",
                ),
                Action(name="Show All w/Baseline", action="show_evolutions_w_bs"),
            ]
            for iso in item.result.isotope_group.iter_isotopes():
                actions = [
                    Action(name="Signal", action="show_evolution_{}".format(iso.name)),
                    Action(
                        name="Equilibration/Signal",
                        action="show_evolution_eq_{}".format(iso.name),
                    ),
                    Action(
                        name="Equilibration/Signal/Baseline",
                        action="show_evolution_eq_bs_{}".format(iso.name),
                    ),
                    Action(
                        name="Signal/Baseline",
                        action="show_evolution_bs_{}".format(iso.name),
                    ),
                ]
                m = MenuManager(*actions, name=iso.name)
                evo_actions.append(m)

            evo = MenuManager(*evo_actions, name="Evolutions")

            success = MenuManager(Action(name="Summary", action="show_summary"), evo)
            return success

    def _get_result_str_image(self):
        if self.item.state == "success":
            return GREEN_BALL
        elif self.item.state == "truncated":
            return ORANGE_BALL

    # ============ non cell editable ============
    def _get_position_text(self):
        at = self.item.analysis_type
        p = self.item.position

        # if at == BLANK_UNKNOWN:
        #     if "," not in p:
        #         p = ""
        #
        if at not in (UNKNOWN, DEGAS, BLANK_UNKNOWN):
            p = ""

        return p

    # ============================================

    def _get_overlap_text(self):
        o, m = self.item.overlap
        if m:
            return "{},{}".format(o, m)
        else:
            if int(o):
                return "{}".format(o)
        return ""

    def _get_aliquot_text(self):
        al = ""
        it = self.item
        if it.aliquot != 0:
            al = make_aliquot_step(it.aliquot, it.step)

        return al

    def _get_ramp_duration_text(self):
        return self._get_number(RAMP_DURATION, fmt="{:n}")

    def _get_beam_diameter_text(self):
        return self._get_number(BEAM_DIAMETER)

    def _get_extract_value_text(self):
        return self._get_number(EXTRACT_VALUE)

    def _get_duration_text(self):
        return self._get_number(DURATION)

    def _get_cleanup_text(self):
        return self._get_number(CLEANUP)

    def _get_pre_cleanup_text(self):
        return self._get_number(PRECLEANUP)

    def _get_post_cleanup_text(self):
        return self._get_number(POSTCLEANUP)

    def _get_cyro_tempurature_text(self):
        return self._get_number(CRYO_TEMP)

    def _get_weight_text(self):
        return self._get_number(WEIGHT)

    def _get_use_cdd_warming_text(self):
        return "Yes" if self.item.use_cdd_warming else "No"

    def _get_number(self, attr, fmt="{:0.2f}"):
        """
        dont display 0.0's
        """
        v = getattr(self.item, attr)
        if v:
            if isinstance(v, str):
                v = float(v)

            return fmt.format(v)
        else:
            return ""


class AutomatedRunSpecAdapter(ExecutedAutomatedRunSpecAdapter):
    def _get_AutomatedRunSpec_menu(self):
        return EDIT_MENU


class RunBlockAdapter(AutomatedRunSpecAdapter):
    columns = [
        ("Identifier", "labnumber"),
        # ('Aliquot', 'aliquot'),
        ("Sample", "sample"),
        ("Position", "position"),
        ("Extract", "extract_value"),
        ("Units", "extract_units"),
        ("Ramp (s)", "ramp_duration"),
        ("Duration (s)", "duration"),
        ("Cleanup (s)", "cleanup"),
        # ('Overlap (s)', 'overlap'),
        ("Beam (mm)", "beam_diameter"),
        ("Pattern", "pattern"),
        ("Extraction", "extraction_script"),
        # ('T_o Offset', 'collection_time_zero_offset'),
        ("Measurement", "measurement_script"),
        ("Conditionals", "conditionals"),
        # ('SynExtraction', 'syn_extraction'),
        ("CDDWarm", "use_cdd_warming"),
        ("Post Eq.", "post_equilibration_script"),
        ("Post Meas.", "post_measurement_script"),
        # ('Options', 'script_options'),
        # ('Comment', 'comment')
    ]


class ExecutedUVAutomatedRunSpecAdapter(ExecutedAutomatedRunSpecAdapter):
    columns = [
        # ('', 'state'),
        ("Identifier", "labnumber"),
        ("Aliquot", "aliquot"),
        ("Sample", "sample"),
        ("Position", "position"),
        ("Extract", "extract_value"),
        ("Units", "extract_units"),
        ("Rep. Rate", "reprate"),
        ("Mask", "mask"),
        ("Attenuator", "attenuator"),
        ("Cleanup (s)", "cleanup"),
        ("Extraction", "extraction_script"),
        ("Measurement", "measurement_script"),
        ("Conditionals", "conditionals"),
        ("SynExtraction", "syn_extraction"),
        ("CDDWarm", "use_cdd_warming"),
        ("Post Eq.", "post_equilibration_script"),
        ("Post Meas.", "post_measurement_script"),
        ("Comment", "comment"),
    ]


class UVAutomatedRunSpecAdapter(ExecutedUVAutomatedRunSpecAdapter):
    pass


# ============= EOF =============================================

# def _columns_default(self):
# cols = self._columns_factory()
#         return cols
#
#     def _columns_factory(self):
#         cols = [
#             ('Labnumber', 'labnumber'),
#             ('Aliquot', 'aliquot'),
#             ('Sample', 'sample'),
#             ('Position', 'position'),
#             ('Extract', 'extract_value'),
#             ('Units', 'extract_units'),
#
#             ('Ramp (s)', 'ramp_duration'),
#             ('Duration (s)', 'duration'),
#             ('Cleanup (s)', 'cleanup'),
#             # ('Overlap (s)', 'overlap'),
#
#             ('Beam (mm)', 'beam_diameter'),
#             ('Pattern', 'pattern'),
#             ('Extraction', 'extraction_script'),
#             # ('T_o Offset', 'collection_time_zero_offset'),
#             ('Measurement', 'measurement_script'),
#             ('Conditionals', 'conditionals'),
#             # ('SynExtraction', 'syn_extraction'),
#             ('CDDWarm', 'use_cdd_warming'),
#             ('Post Eq.', 'post_equilibration_script'),
#             ('Post Meas.', 'post_measurement_script'),
#             # ('Options', 'script_options'),
#             # ('Comment', 'comment')
#         ]
#
#         return colss
# ===============set================
# def _set_labnumber_text(self, v):
#     pass
#
# def _set_sample_text(self, v):
#     pass
# def _set_extraction_script_text(self, v):
#     pass
#
# def _set_measurement_script_text(self, v):
#     pass
#
# def _set_post_measurement_script_text(self, v):
#     pass
#
# def _set_post_equilibration_script_text(self, v):
#     pass
#
# def _set_position_text(self, v):
#     pass
# def _set_ramp_duration_text(self, v):
#     self._set_number(v, 'ramp_duration')
#
# def _set_beam_diameter_text(self, v):
#     self._set_number(v, 'beam_diameter')
#
# def _set_extract_value_text(self, v):
#     self._set_number(v, 'extract_value')
#
# def _set_duration_text(self, v):
#     self._set_number(v, 'duration')
#
# def _set_cleanup_text(self, v):
#     self._set_number(v, 'cleanup')
#
# def _set_use_cdd_warming_text(self, v):
#     self.item.use_cdd_warming = to_bool(v)
#
# def _set_aliquot_text(self, v):
#     self.item.user_defined_aliquot = int(v)

# ==============validate================
# def _validate_aliquot_text(self, v):
#     return self._validate_number(v, 'aliquot', kind=int)
#
# def _validate_extract_value_text(self, v):
#     return self._validate_number(v, 'extract_value')
#
# def _validate_ramp_duration_text(self, v):
#     return self._validate_number(v, 'ramp_duration')
#
# def _validate_beam_diameter_text(self, v):
#     return self._validate_number(v, 'beam_diameter')
#
# def _validate_extract_value_text(self, v):
#     return self._validate_number(v, 'extract_value')
#
# def _validate_duration_text(self, v):
#     return self._validate_number(v, 'duration')
#
# def _validate_cleanup_text(self, v):
#     return self._validate_number(v, 'cleanup')

# ==========helpers==============
# def _set_number(self, v, attr):
#     setattr(self.item, attr, v)
#
# def _validate_number(self, v, attr, kind=float):
#     try:
#         return kind(v)
#     except ValueError:
#         return getattr(self.item, attr)
