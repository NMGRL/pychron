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

from traits.api import Bool, List, HasTraits, Str, Float, Instance

from pychron.core.progress import progress_loader
from pychron.options.options_manager import BlanksOptionsManager, ICFactorOptionsManager, \
    IsotopeEvolutionOptionsManager, \
    FluxOptionsManager
from pychron.options.views import view
from pychron.pipeline.editors.flux_results_editor import FluxResultsEditor
from pychron.pipeline.editors.results_editor import IsoEvolutionResultsEditor
from pychron.pipeline.nodes.figure import FigureNode
from pychron.pychron_constants import NULL_STR


class FitNode(FigureNode):
    use_save_node = Bool(True)
    has_save_node = False

    def _set_saveable(self, state):
        ps = self.plotter_options.get_saveable_aux_plots()
        state.saveable_keys = [p.name for p in ps]
        state.saveable_fits = [p.fit for p in ps]


class FitReferencesNode(FitNode):
    basename = None
    auto_set_items = False

    def run(self, state):

        super(FitReferencesNode, self).run(state)
        if state.canceled:
            return

        self.plotter_options.set_detectors(state.union_detectors)
        if state.references:
            key = lambda x: x.group_id
            for i, (gid, refs) in enumerate(groupby(sorted(state.references, key=key), key=key)):
                if i == 0:
                    editor = self.editor
                else:
                    editor = self._editor_factory()
                    state.editors.append(editor)

                unks = [u for u in state.unknowns if u.group_id == gid]
                editor.set_items(unks, compress=False)
                editor.set_references(list(refs))

        self._set_saveable(state)
        self.editor.force_update(force=True)


class FitBlanksNode(FitReferencesNode):
    editor_klass = 'pychron.pipeline.plot.editors.blanks_editor,BlanksEditor'
    plotter_options_manager_klass = BlanksOptionsManager
    name = 'Fit Blanks'
    basename = 'Blanks'

    def _options_view_default(self):
        return view('Blanks Options')

    def _configure_hook(self):
        pom = self.plotter_options_manager
        if self.unknowns:
            unk = self.unknowns[0]
            names = unk.isotope_keys
            if names:
                names = [NULL_STR] + names
                pom.set_names(names)
                # def _set_saveable(self, state):
                #     super(FitBlanksNode, self)._set_saveable()


ATTRS = ('numerator', 'denominator', 'standard_ratio', 'analysis_type')


class FitICFactorNode(FitReferencesNode):
    editor_klass = 'pychron.pipeline.plot.editors.intercalibration_factor_editor,' \
                   'IntercalibrationFactorEditor'
    plotter_options_manager_klass = ICFactorOptionsManager
    name = 'Fit ICFactor'
    basename = 'ICFactor'

    predefined = List

    def _options_view_default(self):
        return view('ICFactor Options')

    def set_detectors(self, dets):
        self.plotter_options_manager.set_detectors(dets)

    def _set_saveable(self, state):
        super(FitICFactorNode, self)._set_saveable(state)
        ps = self.plotter_options.get_saveable_aux_plots()
        state.saveable_keys = [p.denominator for p in ps]

    # def run(self, state):
    #     super(FitICFactorNode, self).run(state)

    def load(self, nodedict):
        try:
            fits = nodedict['fits']
        except KeyError, e:
            return

        pom = self.plotter_options_manager
        self.plotter_options = pom.selected_options
        self.plotter_options.set_aux_plots(fits)

    def _to_template(self, d):
        d['fits'] = [{'numerator': a.numerator,
                      'denominator': a.denominatior,
                      'standard_ratio': a.standard_ratio,
                      'analysis_type': a.analysis_type}
                     for a in self.plotter_options.aux_plots]


class IsoEvoResult(HasTraits):
    # record_id = Str
    isotope = Str
    fit = Str
    intercept_value = Float
    intercept_error = Float
    percent_error = Float
    regression_str = Str
    goodness = Bool(True)

    analysis = Instance('pychron.processing.analyses.analysis.Analysis')

    @property
    def record_id(self):
        r = ''
        if self.analysis:
            r = self.analysis.record_id
        return r

    @property
    def identifier(self):
        r = ''
        if self.analysis:
            r = self.analysis.identifier
        return r


class FitIsotopeEvolutionNode(FitNode):
    editor_klass = 'pychron.pipeline.plot.editors.isotope_evolution_editor,' \
                   'IsotopeEvolutionEditor'
    plotter_options_manager_klass = IsotopeEvolutionOptionsManager
    name = 'Fit IsoEvo'
    _fits = List

    def _options_view_default(self):
        return view('Iso Evo Options')

    def _configure_hook(self):
        pom = self.plotter_options_manager
        if self.unknowns:
            unk = self.unknowns[0]
            names = unk.isotope_keys
            if names:
                dets = unk.detector_keys
                if dets:
                    names.extend(dets)
                pom.set_names(names)

    def run(self, state):
        # super(FitIsotopeEvolutionNode, self).run(state)

        po = self.plotter_options

        self._fits = list(reversed([pi for pi in po.get_loadable_aux_plots()]))
        fs = progress_loader(state.unknowns, self._assemble_result, threshold=1)

        if self.editor:
            self.editor.analysis_groups = [(ai,) for ai in state.unknowns]

        for ai in state.unknowns:
            ai.graph_id = 0

        self._set_saveable(state)
        # self.name = '{} Fit IsoEvo'.format(self.name)
        # if self.has_save_node and po.confirm_save:
        #     if confirmation_dialog('Would you like to review the iso fits before saving?'):
        #         state.veto = self

        if fs:
            # k = lambda an: an.isotope
            # fs = sort_isotopes(fs, key=k)
            # # fs = [a for _, gs in groupby(fs, key=k)
            # #         for a in gs]
            # _, gs = groupby(fs, key=k)
            # fs = list(gs)[:-1]
            # for x in (gs, (IsoEvoResult(),))
            # for a in x][:-1]
            e = IsoEvolutionResultsEditor(fs)
            state.editors.append(e)

    def _assemble_result(self, xi, prog, i, n):
        po = self.plotter_options

        if prog:
            prog.change_message('Load raw data {}'.format(xi.record_id))

        fits = self._fits
        keys = [fi.name for fi in fits]
        xi.load_raw_data(keys)

        xi.set_fits(fits)
        isotopes = xi.isotopes
        for f in fits:
            k = f.name
            if k in isotopes:
                iso = isotopes[k]
            else:
                iso = next((i.baseline for i in isotopes.values() if i.detector == k), None)

            if iso:
                i, e = iso.value, iso.error
                pe = abs(e / i * 100)
                goodness_threshold = po.goodness_threshold
                goodness = True
                if goodness_threshold:
                    goodness = pe < goodness_threshold

                yield IsoEvoResult(analysis=xi,
                                   intercept_value=i,
                                   intercept_error=e,
                                   percent_error=pe,
                                   goodness=goodness,
                                   regression_str=iso.regressor.tostring(),
                                   fit=f.fit,
                                   isotope=k)


class FitFluxNode(FitNode):
    name = 'Fit Flux'
    editor_klass = FluxResultsEditor
    plotter_options_manager_klass = FluxOptionsManager

    def _options_view_default(self):
        return view('Flux Options')

    def run(self, state):
        editor = super(FitFluxNode, self).run(state)
        if not editor:
            state.canceled = True
            return

        self.name = 'Fit Flux {}'.format(state.irradiation, state.level)
        geom = state.geometry
        monitors = state.flux_monitors

        if monitors:
            lk = self.plotter_options.lambda_k
            state.decay_constants = {'lambda_k_total': lk, 'lambda_k_total_error': 0}

            editor.plotter_options = self.plotter_options
            editor.geometry = geom
            editor.irradiation = state.irradiation
            editor.level = state.level

            editor.set_positions(monitors, state.unknown_positions)
            state.saveable_irradiation_positions = editor.monitor_positions + state.unknown_positions
            editor.predict_values()

# ============= EOF =============================================
