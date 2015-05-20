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
from pychron.processing.plotter_options_manager import IsotopeEvolutionOptionsManager, BlanksOptionsManager
from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor


# class FitNode(BaseNode):
# pass
from pychron.processing.plot.editors.blanks_editor import BlanksEditor


class FitNode(FigureNode):
    use_save_node = Bool(True)

    def _set_saveable(self, state):
        ps = self.plotter_options.get_saveable_plots()
        state.saveable_keys = [p.name for p in ps]
        state.saveable_fits = [p.fit for p in ps]


class FitBlanksNode(FitNode):
    editor_klass = BlanksEditor
    plotter_options_manager_klass = BlanksOptionsManager
    # user_review = Bool(True)

    # _reviewed_flag = False
    name = 'Fit Blanks'

    def run(self, state):
        super(FitBlanksNode, self).run(state)
        if state.references:
            self.editor.set_references(state.references)
            # self.editor.force_update(force=True)

        self.name = 'Fit Blanks {}'.format(self.name)
        self._set_saveable(state)
        state.veto = self



class IsotopeEvolutionNode(FitNode):
    editor_klass = IsotopeEvolutionEditor
    plotter_options_manager_klass = IsotopeEvolutionOptionsManager

    def run(self, state):

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

        self._set_saveable(state)
        self.name = '{} IsoEvo'.format(self.name)

    def post_run(self, state):
        return
        # for ai in state.unknowns:
        #     ai.refit_isotopes(selector.fits)


# ============= EOF =============================================



