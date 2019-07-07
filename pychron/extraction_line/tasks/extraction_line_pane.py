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
from traitsui.api import View, UItem, InstanceEditor, ListEditor, TabularEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter


class CanvasPane(TraitsTaskPane):
    id = 'pychron.extraction_line.canvas'
    name = 'Extraction Line'

    def traits_view(self):
        v = View(UItem('canvas',
                       defined_when='not plugin_canvases',
                       editor=InstanceEditor(),
                       style='custom'),
                 UItem('canvases',
                       defined_when='plugin_canvases',
                       editor=ListEditor(page_name='.display_name',
                                         use_notebook=True),
                       style='custom'))
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


class CryoPane(TraitsDockPane):
    name = 'Cryo'
    id = 'pychron.extraction_line.cryo'

    def traits_view(self):
        v = View(UItem('cryo_manager',
                       editor=InstanceEditor(),
                       style='custom',
                       defined_when='cryo_manager'))
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


class ReadbackAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Cmd', 'last_command'),
               ('Value', 'last_response'),
               ('Timestamp', 'timestamp')]
    font = 'arial 10'
    name_width = Int(75)
    cmd_width = Int(50)
    value_width = Int(100)


class ReadbackPane(TraitsDockPane):
    name = 'Readback'
    id = 'pychron.extraction_line.readback'

    def traits_view(self):
        v = View(UItem('devices',
                       editor=TabularEditor(adapter=ReadbackAdapter(),
                                            auto_update=True,
                                            editable=False)))
        return v

# ============= EOF =============================================
