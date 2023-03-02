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
from traits.api import HasTraits, Instance
from traitsui.api import View, Item, VGroup, Spring, HGroup, ButtonEditor
from traitsui.item import UItem

from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.core.ui.enum_editor import myEnumEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pychron_constants import (
    POSTCLEANUP,
    CLEANUP,
    PRECLEANUP,
    CRYO_TEMP,
    OVERLAP,
    LIGHT_VALUE,
    USE_CDD_WARMING,
    POSITION,
    PATTERN,
    EXTRACT_VALUE,
    EXTRACT_UNITS,
    RAMP_DURATION,
    DURATION,
    BEAM_DIAMETER,
    TEMPLATE,
    DISABLE_BETWEEN_POSITIONS,
)

POSITION_TOOLTIP = """Set the position for this analysis or group of analyses.
Examples:
1.  4 or p4 (goto position 4)
2.  3,4,5 (goto positions 3,4,5. treat as one analysis)
3.  7-12 (goto positions 7,8,9,10,11,12. treat as individual analyses)
4.  7:12 (same as #3)
5.  10:16:2 (goto positions 10,12,14,16. treat as individual analyses)
6.  D1 (drill position 1)
7.  T1-2 (goto named position T1-2 i.e transect 1, point 2)
8.  L3 (trace path L3)
9.  1-6;9;11;15-20 (combination of rules 2. and 3. treat all positions as individual analyses)
10. 1.0,2.0 (goto the point defined by x,y[,z]. Use ";" to treat multiple points as one analysis e.g 1.0,2.0;3.0,4.0)
11. s1 or S1 (goto Scan 1 via Chromium Laser)
"""

PATTERN_TOOLTIP = 'Please select a pattern from Remote or Local Patterns. \
If unsure from which group to choice use a "Remote" pattern'


class FactoryView(HasTraits):
    model = Instance("pychron.experiment.automated_run.factory.AutomatedRunFactory")

    def trait_context(self):
        return {"object": self.model}

    def traits_view(self):
        v = View(self._get_group())
        return v

    def _get_group(self):
        egrp = BorderVGroup(
            HGroup(
                Spring(springy=False, width=33),
                Item(
                    EXTRACT_VALUE,
                    label="Extract",
                    tooltip="Set the extract value in extract units",
                    enabled_when="extractable",
                ),
                Item(
                    EXTRACT_UNITS,
                    show_label=False,
                    editor=myEnumEditor(name="extract_units_names"),
                ),
                Item(RAMP_DURATION, label="Ramp Dur. (s)"),
            ),
            Item(
                DURATION,
                label="Extract Duration (s)",
                tooltip="Set the number of seconds to run the extraction device.",
            ),
            Item(BEAM_DIAMETER),
            label="Fusion",
        )

        extract_grp = BorderVGroup(
            egrp,
            self._step_heat_group(),
            self._position_group(),
            BorderHGroup(
                VGroup(
                    HGroup(
                        Item(
                            USE_CDD_WARMING,
                            label="CDD Warm",
                            tooltip="Use the CDD warming routine at end of measurement",
                        ),
                        # Item('collection_time_zero_offset',
                        #      label='T_o offset (s)',
                        #      tooltip='# of seconds afer inlet opens to set time zero'),
                        Item(
                            OVERLAP,
                            label="Overlap (s)",
                            tooltip="Duration to wait before staring next run",
                        ),
                        Item(LIGHT_VALUE, label="Lighting"),
                        Item(CRYO_TEMP, label="Cryo Temp. (K)"),
                    ),
                    Item(
                        DISABLE_BETWEEN_POSITIONS,
                        tooltip="Disable the extraction device when moving between positions.  WARNING this will only "
                        "work if the extraction script is configured properly.",
                        label="Disable Between Positions",
                    ),
                ),
                label="Extras",
            ),
            label="Extract",
        )
        cleanup_grp = BorderVGroup(
            Item(PRECLEANUP, label="Pre Cleanup (s)"),
            Item(
                CLEANUP,
                label="Cleanup (s)",
                tooltip="Set the number of seconds to getter the sample gas",
            ),
            Item(POSTCLEANUP, label="Post Cleanup (s)"),
            label="Cleanup",
        )

        post_measurement_group = BorderVGroup(
            Item("delay_after"), label="Post Measurement"
        )
        grp = VGroup(extract_grp, cleanup_grp, post_measurement_group)
        return grp

    def _position_group(self):
        grp = BorderHGroup(
            Item(POSITION, tooltip=POSITION_TOOLTIP),
            UItem(
                PATTERN, tooltip=PATTERN_TOOLTIP, editor=myEnumEditor(name="patterns")
            ),
            UItem(
                "edit_pattern", editor=ButtonEditor(label_value="edit_pattern_label")
            ),
            label="Positioning",
        )
        return grp

    def _step_heat_group(self):
        grp = BorderHGroup(
            UItem(
                TEMPLATE,
                editor=myEnumEditor(name="templates"),
            ),
            UItem(
                "edit_template", editor=ButtonEditor(label_value="edit_template_label")
            ),
            icon_button_editor(
                "apply_stepheat",
                "arrow_right",
                enabled_when="_selected_runs",
                tooltip="Apply step heat template to selected",
            ),
            label="Step Heating",
        )
        return grp

        # ============= EOF =============================================
