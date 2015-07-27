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
from traits.api import Bool, List, HasTraits, Str, Float, Instance
# ============= standard library imports ========================
from itertools import groupby
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.progress import progress_loader
from pychron.pipeline.editors.flux_results_editor import FluxResultsEditor, FluxPosition
from pychron.pipeline.editors.results_editor import IsoEvolutionResultsEditor
from pychron.pipeline.nodes.figure import FigureNode
from pychron.processing.flux.utilities import mean_j
from pychron.pipeline.options.plotter_options_manager import IsotopeEvolutionOptionsManager, BlanksOptionsManager, \
    ICFactorOptionsManager, FluxOptionsManager


class FitNode(FigureNode):
    use_save_node = Bool(True)
    has_save_node = False

    def _set_saveable(self, state):
        ps = self.plotter_options.get_saveable_aux_plots()
        state.saveable_keys = [p.name for p in ps]
        state.saveable_fits = [p.fit for p in ps]


class FitReferencesNode(FitNode):
    basename = None

    def run(self, state):

        super(FitReferencesNode, self).run(state)
        if state.canceled:
            return

        self.plotter_options.set_detectors(state.union_detectors)
        if state.references:
            self.editor.set_references(state.references)

        # self.name = 'Fit {} {}'.format(self.basename, self.name)
        self._set_saveable(state)

        # if self.has_save_node:
        #     if self.plotter_options.confirm_save:
        #         if confirmation_dialog('Would you like to review the {} before saving?'.format(self.basename)):
        #             state.veto = self
        #         else:
        #             self.editor.force_update(force=True)
        #     else:
        self.editor.force_update(force=True)


class FitBlanksNode(FitReferencesNode):
    editor_klass = 'pychron.pipeline.plot.editors.blanks_editor,BlanksEditor'
    plotter_options_manager_klass = BlanksOptionsManager
    name = 'Fit Blanks'
    basename = 'Blanks'

    def _configure_hook(self):
        pom = self.plotter_options_manager
        if self.unknowns:
            unk = self.unknowns[0]
            names = unk.isotope_keys
            if names:
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
        self.plotter_options = pom.plotter_options
        self.plotter_options.set_aux_plots(fits)


class IsoEvoResult(HasTraits):
    # record_id = Str
    isotope = Str
    fit = Str
    intercept_value = Float
    intercept_error = Float
    regression_str = Str

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
        super(FitIsotopeEvolutionNode, self).run(state)

        po = self.plotter_options

        self._fits = [pi for pi in po.get_loadable_aux_plots()]
        fs = progress_loader(state.unknowns, self._assemble_result)

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
            k = lambda an: an.isotope
            fs = sort_isotopes(fs, key=k)
            fs = [a for _, gs in groupby(fs, key=k)
                  for x in (gs, (IsoEvoResult(),))
                  for a in x][:-1]
            e = IsoEvolutionResultsEditor(fs)
            state.editors.append(e)

    def _assemble_result(self, xi, prog, i, n):

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

            yield IsoEvoResult(analysis=xi,
                               intercept_value=nominal_value(iso.uvalue),
                               intercept_error=std_dev(iso.uvalue),
                               regression_str=iso.regressor.tostring(),
                               fit=f.fit,
                               isotope=k)


class FitFluxNode(FitNode):
    name = 'Fit Flux'
    editor_klass = FluxResultsEditor
    plotter_options_manager_klass = FluxOptionsManager

    # options = Instance(FluxOptions, ())

    # def configure(self, refresh=True):
    #
    #     return True

    def run(self, state):
        editor = super(FitFluxNode, self).run(state)
        if not editor:
            state.canceled = True
            return

        self.name = 'Fit Flux {}'.format(state.irradiation, state.level)
        geom = state.geometry

        monitors = state.flux_monitors
        # editor.analyses = monitors
        # monitor_positions = []
        if monitors:
            opt = self.plotter_options
            monage = opt.monitor_age * 1e6
            lk = opt.lambda_k
            ek = opt.error_kind
            state.decay_constants = {'lambda_k_total': lk, 'lambda_k_total_error': 0}
            # editor = FluxResultsEditor(options=self.options,
            #                            plotter_options=self.plotter_options)
            key = lambda x: x.identifier
            poss = []
            for identifier, ais in groupby(sorted(monitors, key=key), key=key):
                ais = list(ais)
                n = len(ais)

                ref = ais[0]
                j = ref.j
                ip = ref.irradiation_position
                sample = ref.sample

                x, y, r, idx = geom[ip - 1]
                mj = mean_j(ais, ek, monage, lk)

                p = FluxPosition(identifier=identifier,
                                 irradiation=state.irradiation,
                                 level=state.level,
                                 sample=sample, hole_id=ip,
                                 saved_j=nominal_value(j),
                                 saved_jerr=std_dev(j),
                                 mean_j=nominal_value(mj),
                                 mean_jerr=std_dev(mj),
                                 analyses=ais,
                                 x=x, y=y,
                                 n=n)
                poss.append(p)

                # for unk_pos in state.unknown_positions:
                # print unk_pos

                # print identifier, irradiation_position, j, mj, n
                # editor.add_position(identifier, ip, sample, j, mj, n)
            editor.geometry = geom
            state.saveable_irradiation_positions = poss + state.unknown_positions
            editor.set_positions(poss, state.unknown_positions)
            editor.predict_values()

            # if self.has_save_node and self.plotter_options.confirm_save:
            #     if confirmation_dialog('Would you like to review the flux fits before saving?'):
            # state.veto = self

            # state.editors.append(editor)
            # state.prev_node_label = 'Flux'
# ============= EOF =============================================
