# ===============================================================================
# Copyright 2020 ross
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
from traits.api import Enum

from pychron.gis.options import GISOptionsManager
from pychron.gis.qgis_figure_editor import GISFigureEditor
from pychron.pipeline.nodes import GroupingNode
from pychron.pipeline.nodes.figure import FigureNode


class SampleGroupingNode(GroupingNode):
    name = 'Sample Grouping'
    keys = ('Material',
            'Sample',
            'Comment',
            'SubGroup',
            'Group Name',
            'Label Name',
            'No Grouping')
    attribute = Enum('FeatureGroup',)


class GISNode(FigureNode):
    name = 'GIS'
    editor_klass = 'pychron.gis.qgis_figure_editor, GISFigureEditor'
    plotter_options_manager_klass = GISOptionsManager

    def refresh(self):
        self.editor.refresh_map()

    def run(self, state):
        editor = GISFigureEditor()
        editor.plotter_options = self.plotter_options
        editor.set_items(state.unknowns)
        editor.load()
        state.editors.append(editor)
        self.editor = editor

# ============= EOF =============================================
