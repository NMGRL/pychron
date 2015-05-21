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
from pychron.core.confirmation import confirmation_dialog
from pychron.pipeline.nodes.figure import FigureNode
from pychron.processing.plotter_options_manager import IsotopeEvolutionOptionsManager, BlanksOptionsManager, \
    ICFactorOptionsManager


class FitNode(FigureNode):
    use_save_node = Bool(True)

    def _set_saveable(self, state):
        ps = self.plotter_options.get_saveable_plots()
        state.saveable_keys = [p.name for p in ps]
        state.saveable_fits = [p.fit for p in ps]


class FitReferencesNode(FitNode):
    basename = None
    has_save_node = False
    
    def run(self, state):
        super(FitReferencesNode, self).run(state)
        if state.references:
            self.editor.set_references(state.references)
            # self.editor.force_update(force=True)

        self.name = 'Fit {} {}'.format(self.basename, self.name)
        self._set_saveable(state)

        if self.has_save_node:
            if confirmation_dialog('Would you like to review the {} before saving?'.format(self.basename)):
                state.veto = self


class FitBlanksNode(FitReferencesNode):
    editor_klass = 'pychron.processing.plot.editors.blanks_editor,BlanksEditor'
    plotter_options_manager_klass = BlanksOptionsManager
    name = 'Fit Blanks'
    basename = 'Blanks'


class FitICFactorNode(FitReferencesNode):
    editor_klass = 'pychron.processing.plot.editors.intercalibration_factor_editor,' \
                   'IntercalibrationFactorEditor'
    plotter_options_manager_klass = ICFactorOptionsManager
    name = 'Fit ICFactor'
    basename = 'ICFactor'


    # def run(self, state):
    #     pass

class FitIsotopeEvolutionNode(FitNode):
    editor_klass = 'pychron.processing.plot.editors.isotope_evolution_editor,' \
                   'IsotopeEvolutionEditor'
    plotter_options_manager_klass = IsotopeEvolutionOptionsManager
    name = 'Fit IsoEvo'

    def run(self, state):

        # graph_ids = [(ai.uuid, idx) for idx, ai in enumerate(state.unknowns)]
        super(FitIsotopeEvolutionNode, self).run(state)

        for idx, ai in enumerate(state.unknowns):
            # ai.graph_id = idx
            po = self.plotter_options

            keys = [pi.name for pi in po.get_aux_plots()]
            ai.load_raw_data(keys)

            fits = [pi for pi in po.get_aux_plots()]
            ai.set_fits(fits)

        self.editor.analysis_groups = [(ai,) for ai in state.unknowns]
        for ai in state.unknowns:
            ai.graph_id = 0

        self._set_saveable(state)
        self.name = '{} Fit IsoEvo'.format(self.name)
        if confirmation_dialog('Would you like to review the iso fits before saving?'):
            state.veto = self


# ============= EOF =============================================



