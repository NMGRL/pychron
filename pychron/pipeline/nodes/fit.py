# ===============================================================================
# Copyright 2015 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.nodes.figure import FigureNode
from pychron.processing.plotter_options_manager import IsotopeEvolutionOptionsManager
from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor


# class FitNode(BaseNode):
# pass


class IsotopeEvolutionNode(FigureNode):
    editor_klass = IsotopeEvolutionEditor
    plotter_options_manager_klass = IsotopeEvolutionOptionsManager

    def run(self, state):
        # selector = IsoEvoFitSelector()
        # selector.load_fits()

        for idx, ai in enumerate(state.unknowns):
            ai.graph_id = idx
            po = self.plotter_options

            keys = [pi.name for pi in po.get_aux_plots()]
            ai.load_raw_data(keys)

        super(IsotopeEvolutionNode, self).run(state)


    def post_run(self, state):
        return
        # for ai in state.unknowns:
        #     ai.refit_isotopes(selector.fits)


# ============= EOF =============================================



