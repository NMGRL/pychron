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
from pyface.qt.QtCore import QSize
from pyface.qt.QtWidgets import QSizePolicy
from traits.api import Any, Int
from traitsui.api import (
    View,
    UItem,
    InstanceEditor,
    ListEditor,
    TabularEditor,
    VGroup,
)

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.envisage.icon_button_editor import icon_button_editor


class CanvasPane(TraitsTaskPane):
    id = "pychron.extraction_line.canvas"
    name = "Extraction Line"

    def create_contents(self, parent):
        """Override to set Qt-level size policy."""
        control = super().create_contents(parent)
        
        # Force Qt to expand - use massive minimum size as hard floor
        control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control.setMinimumSize(1200, 900)
        
        return control

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
                editor=ListEditor(
                    page_name=".display_name",
                    use_notebook=True,
                    editor=InstanceEditor(),
                ),
                style="custom",
            ),
            resizable=True,
        )
        return v


class CanvasDockPane(TraitsDockPane):
    id = "pychron.extraction_line.canvas_dock"
    name = "Extraction Line Canvas"
    canvas = Any

    def traits_view(self) -> View:
        return View(UItem("canvas", editor=InstanceEditor(), style="custom"), resizable=True)


class HeaterPane(TraitsDockPane):
    name = "Heaters"
    id = "pychron.extraction_line.heater"

    def traits_view(self):
        v = View(
            UItem(
                "heater_manager",
                editor=InstanceEditor(),
                style="custom",
                defined_when="heater_manager",
            )
        )
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
    name = "Pump"
    id = "pychron.extraction_line.pump"

    def traits_view(self):
        v = View(
            UItem(
                "pump_manager",
                editor=InstanceEditor(),
                style="custom",
                defined_when="pump_manager",
            )
        )
        return v


class ExplanationPane(TraitsDockPane):
    name = "Explanation"
    id = "pychron.extraction_line.explanation"

    def traits_view(self):
        v = View(
            UItem(
                "canvas_manager",
                editor=InstanceEditor(),
                style="custom",
            )
        )
        return v


class InspectorPane(TraitsDockPane):
    name = "Inspector"
    id = "pychron.extraction_line.inspector"

    def traits_view(self):
        v = View(
            UItem(
                "canvas_manager",
                editor=InstanceEditor(),
                style="custom",
            )
        )
        return v


class ReadbackPane(TraitsDockPane):
    name = "Readback"
    id = "pychron.extraction_line.readback"

    def traits_view(self):
        v = View(
            UItem(
                "readback_manager",
                editor=InstanceEditor(),
                style="custom",
                defined_when="readback_manager",
            )
        )
        return v


class EditorPane(TraitsDockPane):
    name = "Editor"
    id = "pychron.extraction_line.editor"

    def traits_view(self):
        v = View(
            UItem(
                "editor_view",
                editor=InstanceEditor(),
                style="custom",
            )
        )
        return v


# ============= EOF =============================================
