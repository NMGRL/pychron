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
from traits.api import Bool
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

    use_save_node = Bool(True)

    def run(self, state):
        state.saveable_keys = self.plotter_options.get_saveable_plots()

        # graph_ids = [(ai.uuid, idx) for idx, ai in enumerate(state.unknowns)]

        for idx, ai in enumerate(state.unknowns):
            # ai.graph_id = idx
            po = self.plotter_options

            keys = [pi.name for pi in po.get_aux_plots()]
            ai.load_raw_data(keys)

            fits = [pi for pi in po.get_aux_plots()]
            ai.set_fits(fits)

        super(IsotopeEvolutionNode, self).run(state)

        self.editor.analysis_groups = [(ai,) for ai in state.unknowns]
        for ai in state.unknowns:
            ai.graph_id = 0

    def post_run(self, state):
        return
        # for ai in state.unknowns:
        #     ai.refit_isotopes(selector.fits)


# ============= EOF =============================================



