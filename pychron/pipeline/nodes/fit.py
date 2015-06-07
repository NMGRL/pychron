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
from itertools import groupby

from traits.api import Bool, List, HasTraits, Str, Float

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.confirmation import confirmation_dialog
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.pipeline.editors.results_editor import IsoEvolutionResultsEditor
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

        self.plotter_options.set_detectors(state.union_detectors)
        if state.references:
            self.editor.set_references(state.references)

        self.name = 'Fit {} {}'.format(self.basename, self.name)
        self._set_saveable(state)

        if self.has_save_node:
            if confirmation_dialog('Would you like to review the {} before saving?'.format(self.basename)):
                state.veto = self
            else:
                self.editor.force_update(force=True)


class FitBlanksNode(FitReferencesNode):
    editor_klass = 'pychron.processing.plot.editors.blanks_editor,BlanksEditor'
    plotter_options_manager_klass = BlanksOptionsManager
    name = 'Fit Blanks'
    basename = 'Blanks'
    # def _set_saveable(self, state):
    #     super(FitBlanksNode, self)._set_saveable()


ATTRS = ('numerator', 'denominator', 'standard_ratio', 'analysis_type')


class FitICFactorNode(FitReferencesNode):
    editor_klass = 'pychron.processing.plot.editors.intercalibration_factor_editor,' \
                   'IntercalibrationFactorEditor'
    plotter_options_manager_klass = ICFactorOptionsManager
    name = 'Fit ICFactor'
    basename = 'ICFactor'

    predefined = List

    def set_detectors(self, dets):
        self.plotter_options_manager.set_detectors(dets)

    def _set_saveable(self, state):
        super(FitICFactorNode, self)._set_saveable(state)
        ps = self.plotter_options.get_saveable_plots()
        state.saveable_keys = [p.denominator for p in ps]

    def run(self, state):
        super(FitICFactorNode, self).run(state)

    def load(self, nodedict):
        try:
            fits = nodedict['fits']
        except KeyError, e:
            print 'afs', e

        pom = self.plotter_options_manager
        self.plotter_options = pom.plotter_options
        self.plotter_options.set_aux_plots(fits)


class IsoEvoResult(HasTraits):
    record_id = Str
    isotope = Str
    fit = Str
    intercept_value = Float
    intercept_error = Float
    regression_str = Str
    identifier = Str
    # isotopes = List
    # fits = List

    # def __init__(self, fits, *args, **kw):
    #     super(IsoEvoResult, self).__init__(*args, **kw)
        # self.isotopes = [f.name for f in fits]
        # for f in fits:
        #     setattr(self, '{}Fit'.format(f.name), f.fit)
        # self.fits = [f.fit for f in fits]


class FitIsotopeEvolutionNode(FitNode):
    editor_klass = 'pychron.processing.plot.editors.isotope_evolution_editor,' \
                   'IsotopeEvolutionEditor'
    plotter_options_manager_klass = IsotopeEvolutionOptionsManager
    name = 'Fit IsoEvo'

    def run(self, state):

        # graph_ids = [(ai.uuid, idx) for idx, ai in enumerate(state.unknowns)]
        super(FitIsotopeEvolutionNode, self).run(state)

        fs = []

        for idx, ai in enumerate(state.unknowns):
            # ai.graph_id = idx
            po = self.plotter_options

            keys = [pi.name for pi in po.get_saveable_aux_plots()]
            ai.load_raw_data(keys)

            fits = [pi for pi in po.get_saveable_aux_plots()]
            ai.set_fits(fits)
            for f in fits:
                k = f.name
                iso = ai.isotopes[k]
                fs.append(IsoEvoResult(record_id=ai.record_id,
                                       identifier=ai.identifier,
                                       intercept_value=iso.value,
                                       intercept_error=iso.error,
                                       regression_str=iso.regressor.make_equation(),
                                       fit=f.fit,
                                       isotope=k))

            # fs.append(IsoEvoResult(fits, record_id=ai.record_id, identifier=ai.identifier))

        self.editor.analysis_groups = [(ai,) for ai in state.unknowns]
        for ai in state.unknowns:
            ai.graph_id = 0

        self._set_saveable(state)
        self.name = '{} Fit IsoEvo'.format(self.name)
        if confirmation_dialog('Would you like to review the iso fits before saving?'):
            state.veto = self

        if fs:
            k = lambda x: x.isotope
            # c = lambda x,y:
            # fs = sorted(fs, key=k, cmp=c)
            fs = sort_isotopes(fs, key=k)
            fs = [a for _, gs in groupby(fs, key=k)
                        for x in (gs, (IsoEvoResult(),))
                            for a in x][:-1]
            e = IsoEvolutionResultsEditor(fs)
            state.editors.append(e)

# ============= EOF =============================================
