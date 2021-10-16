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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Any, Int
from traitsui.api import View, UItem, InstanceEditor, ListEditor, TabularEditor, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.envisage.icon_button_editor import icon_button_editor


class CanvasPane(TraitsTaskPane):
    id = "pychron.extraction_line.canvas"
    name = "Extraction Line"

    def traits_view(self):
        v = View(
            UItem(
                "canvas",
                defined_when="not plugin_canvases",
                editor=InstanceEditor(),
                style="custom",
            ),
            UItem(
                "canvases",
                defined_when="plugin_canvases",
                editor=ListEditor(page_name=".display_name", use_notebook=True),
                style="custom",
            ),
        )
        return v


class CanvasDockPane(TraitsDockPane):
    id = "pychron.extraction_line.canvas_dock"
    name = "Extraction Line Canvas"
    canvas = Any

    def traits_view(self):
        v = View(UItem("canvas", editor=InstanceEditor(), style="custom", width=500))
        return v


class HeaterPane(TraitsDockPane):
    name = 'Heaters'
    id = 'pychron.extraction_line.heater'

    def traits_view(self):
        v = View(UItem('heater_manager',
                       editor=InstanceEditor(),
                       style='custom',
                       defined_when='heater_manager'))
        return v


class CryoPane(TraitsDockPane):
    name = "Cryo"
    id = "pychron.extraction_line.cryo"

    def traits_view(self):
        v = View(
            UItem(
                "cryo_manager",
                editor=InstanceEditor(),
                style="custom",
                defined_when="cryo_manager",
            )
        )
        return v


class GaugePane(TraitsDockPane):
    name = "Gauges"
    id = "pychron.extraction_line.gauges"

    def traits_view(self):
        v = View(
            UItem(
                "gauge_manager",
                editor=InstanceEditor(),
                style="custom",
                height=125,
                defined_when="gauge_manager",
            )
        )
        return v


class PumpPane(TraitsDockPane):
    name = 'Pumps'
    id = 'pychron.extraction_line.pumps'

    def traits_view(self):
        v = View(UItem('pump_manager',
                       editor=InstanceEditor(),
                       style='custom',
                       height=125,
                       defined_when='pump_manager'))
        return v


class ExplanationPane(TraitsDockPane):
    name = "Explanation"
    id = "pychron.extraction_line.explanation"

    def traits_view(self):
        v = View(UItem("explanation", style="custom"))
        return v


class ReadbackAdapter(TabularAdapter):
    columns = [
        ("Name", "name"),
        ("Cmd", "last_command"),
        ("Value", "last_response"),
        ("Timestamp", "timestamp"),
    ]
    font = "arial 10"
    name_width = Int(75)
    cmd_width = Int(50)
    value_width = Int(100)


class ReadbackPane(TraitsDockPane):
    name = "Readback"
    id = "pychron.extraction_line.readback"

    def traits_view(self):
        v = View(
            UItem(
                "devices",
                editor=TabularEditor(
                    adapter=ReadbackAdapter(), auto_update=True, editable=False
                ),
            )
        )
        return v


class EditorPane(TraitsDockPane):
    name = "Editor"
    id = "pychron.extraction_line.editor"

    def traits_view(self):
        egrp = VGroup(
            BorderHGroup(
                icon_button_editor("increment_down_x", "arrow_left"),
                icon_button_editor("increment_up_x", "arrow_right"),
                UItem("x_magnitude"),
                label="X",
            ),
            BorderHGroup(
                icon_button_editor("increment_up_y", "arrow_up"),
                icon_button_editor("increment_down_y", "arrow_down"),
                UItem("y_magnitude"),
                label="Y",
            ),
            BorderHGroup(
                UItem("width"),
                icon_button_editor("width_increment_minus_button", "delete"),
                icon_button_editor("width_increment_plus_button", "add"),
                label="Width",
            ),
            BorderHGroup(
                UItem("height"),
                icon_button_editor("height_increment_minus_button", "delete"),
                icon_button_editor("height_increment_plus_button", "add"),
                label="Height",
            ),
            UItem("color"),
            UItem("save_button"),
        )

        agrp = BorderVGroup(
            UItem("add_item_button"),
            UItem("new_item_kind"),
            UItem("new_item", style="custom", editor=InstanceEditor(view="edit_view")),
            label="New Item",
        )
        g = VGroup(
            UItem(
                "groups",
                style="custom",
                editor=ListEditor(
                    use_notebook=True,
                    page_name=".name",
                    selected="selected_group",
                    editor=InstanceEditor(),
                ),
            )
        )

        v = View(VGroup(UItem('edit_mode'),
                        VGroup(g, agrp, egrp, enabled_when='edit_mode')))
        return v


# ============= EOF =============================================
