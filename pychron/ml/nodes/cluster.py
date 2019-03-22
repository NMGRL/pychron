# ===============================================================================
# Copyright 2019 ross
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
from pychron.ml.options.cluster import ClusterOptionsManager
from pychron.pipeline.nodes.figure import FigureNode


class ClusterNode(FigureNode):
    name = 'Cluster'
    editor_klass = 'pychron.ml.editors.cluster,ClusterEditor'
    plotter_options_manager_klass = ClusterOptionsManager

    # def _options_view_default(self):
    #     return view('Flux Options')

    def run(self, state):
        self.editor = editor = self._editor_factory()
        editor.plotter_options = self.plotter_options
        state.editors.append(editor)
        if not editor:
            state.canceled = True
            return

        editor.set_items(state.unknowns)
        # self.name = 'Flux Visualization {}'.format(state.irradiation, state.level)
        # geom = state.geometry

        # ps = state.monitor_positions

        # if ps:
        #     po = self.plotter_options
        #
        #     editor.plotter_options = po
        #     editor.geometry = geom
        #     editor.irradiation = state.irradiation
        #     editor.level = state.level
        #     editor.holder = state.holder
        #
        #     editor.set_positions(ps)
        #     editor.name = 'Flux Visualization: {}{}'.format(state.irradiation, state.level)

# ============= EOF =============================================
