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
from traits.api import Any
from traitsui.api import View, UItem, InstanceEditor


# ============= standard library imports ========================
# ============= local library imports  ==========================


class CanvasPane(TraitsTaskPane):
    id = 'pychron.extraction_line.canvas'
    name = 'Extraction Line'

    def traits_view(self):
        v = View(UItem('canvas', style='custom'))
        return v


class CanvasDockPane(TraitsDockPane):
    id = 'pychron.extraction_line.canvas_dock'
    name = 'Extraction Line Canvas'
    canvas = Any

    def traits_view(self):
        v = View(UItem('canvas',
                       editor=InstanceEditor(),
                       style='custom',
                       width=500))
        return v


class GaugePane(TraitsDockPane):
    name = 'Gauges'
    id = 'pychron.extraction_line.gauges'

    def traits_view(self):
        v = View(UItem('gauge_manager',
                       editor=InstanceEditor(),
                       style='custom',
                       height=125,
                       defined_when='gauge_manager'))
        return v


class ExplanationPane(TraitsDockPane):
    name = 'Explanation'
    id = 'pychron.extraction_line.explanation'

    def traits_view(self):
        v = View(UItem('explanation',
                       style='custom'))
        return v

# ============= EOF =============================================
