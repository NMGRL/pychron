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
from numpy import array, vstack
from traits.api import Bool, List, HasTraits, Str, Float, Instance, Int
# ============= standard library imports ========================
from itertools import groupby
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.confirmation import confirmation_dialog
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.progress import progress_loader
from pychron.core.regression.flux_regressor import PlaneFluxRegressor
from pychron.core.regression.flux_regressor import BowlFluxRegressor
from pychron.pipeline.editors.flux_results_editor import FluxResultsEditor, FluxPosition
from pychron.pipeline.editors.results_editor import IsoEvolutionResultsEditor
from pychron.pipeline.nodes.figure import FigureNode
from pychron.processing.flux.utilities import mean_j
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
    editor_klass = 'pychron.processing.plot.editors.isotope_evolution_editor,' \
                   'IsotopeEvolutionEditor'
    plotter_options_manager_klass = IsotopeEvolutionOptionsManager
    name = 'Fit IsoEvo'
    _fits = List

    def run(self, state):
        super(FitIsotopeEvolutionNode, self).run(state)

        po = self.plotter_options
        self._fits = [pi for pi in po.get_saveable_aux_plots()]
        fs = progress_loader(state.unknowns, self._assemble_result)

        if self.editor:
            self.editor.analysis_groups = [(ai,) for ai in state.unknowns]

        for ai in state.unknowns:
            ai.graph_id = 0

        self._set_saveable(state)
        self.name = '{} Fit IsoEvo'.format(self.name)
        if po.confirm_save:
            if confirmation_dialog('Would you like to review the iso fits before saving?'):
                state.veto = self

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
            prog.change_message.format('Load raw data {}'.format(xi.record_id))

        fits = self._fits
        keys = [fi.name for fi in fits]
        xi.load_raw_data(keys)

        xi.set_fits(fits)
        for f in fits:
            k = f.name
            iso = xi.isotopes[k]
            yield IsoEvoResult(analysis=xi,
                               intercept_value=nominal_value(iso.uvalue),
                               intercept_error=std_dev(iso.uvalue),
                               regression_str=iso.regressor.make_equation(),
                               fit=f.fit,
                               isotope=k)


class FitFluxNode(FitNode):
    error_kind = 'SD'
    monitor_age = 28.201
    lambda_k = 5.464e-10
    model_kind = 'Plane'

    predicted_j_error_type = 'SD'
    use_weighted_fit = Bool(False)
    monte_carlo_ntrials = Int(10)
    use_monte_carlo = Bool(False)

    def run(self, state):
        geom = state.geometry

        monitors = state.flux_monitors
        # monitor_positions = []
        if monitors:
            monage = self.monitor_age * 1e6
            lk = self.lambda_k
            ek = self.error_kind

            editor = FluxResultsEditor()
            key = lambda x: x.identifier
            poss = []
            for identifier, ais in groupby(sorted(monitors, key=key), key=key):
                ais = list(ais)
                n = len(ais)

                ref = ais[0]
                j = ref.j
                ip = ref.irradiation_position
                sample = ref.sample

                x, y, r, idx = geom[ip-1]
                mj = mean_j(ais, ek, monage, lk)
                p = FluxPosition(identifier=identifier, sample=sample, hole_id=ip,
                                 saved_j=nominal_value(j),
                                 saved_jerr=std_dev(j),
                                 mean_j=nominal_value(mj),
                                 mean_jerr=std_dev(mj),
                                 x=x, y=y,
                                 n=n)
                poss.append(p)
                # print identifier, irradiation_position, j, mj, n
                # editor.add_position(identifier, ip, sample, j, mj, n)
            self._predict_values(poss, poss)

            editor.positions = poss
            state.editors.append(editor)

    def _predict_values(self, monitor_positions, all_positions):
        try:
            x, y, z, ze = array([(pos.x, pos.y, pos.mean_j, pos.mean_jerr)
                                 for pos in monitor_positions
                                 if pos.use]).T

        except ValueError:
            # self.debug('no monitor positions to fit')
            return

        n = x.shape[0]
        if n > 3:
            # n = z.shape[0] * 10
            # r = max((max(abs(x)), max(abs(y))))
            # r *= 1.25
            reg = self._regressor_factory(x, y, z, ze)
            self._regressor = reg
        else:
            # self.warning('not enough monitor positions. at least 3 required. Currently only {} active'.format(n))
            return

        if self.use_monte_carlo:
            from pychron.core.stats.monte_carlo import monte_carlo_error_estimation

            pts = array([[p.x, p.y] for p in all_positions])
            nominals = reg.predict(pts)
            errors = monte_carlo_error_estimation(reg, nominals, pts,
                                                  ntrials=self.monte_carlo_ntrials)
            for p, j, je in zip(all_positions, nominals, errors):
                oj = p.saved_j

                p.j = j
                p.jerr = je

                p.dev = (oj - j) / j * 100
        else:
            for p in all_positions:
                j = reg.predict([(p.x, p.y)])[0]
                je = reg.predict_error([[(p.x, p.y)]])[0]
                oj = p.saved_j

                p.j = j
                p.jerr = je

                p.dev = (oj - j) / j * 100

    def _regressor_factory(self, x, y, z, ze):
        if self.model_kind == 'Bowl':
            # from pychron.core.regression.flux_regressor import BowlFluxRegressor
            klass = BowlFluxRegressor
        else:
            # from pychron.core.regression.flux_regressor import PlaneFluxRegressor
            klass = PlaneFluxRegressor

        x = array(x)
        y = array(y)
        xy = vstack((x, y)).T
        wf = self.use_weighted_fit
        if wf:
            ec = 'SD'
        else:
            ec = self.predicted_j_error_type

        reg = klass(xs=xy, ys=z, yserr=ze,
                    error_calc_type=ec,
                    use_weighted_fit=wf)
        # error_calc_type=self.tool.predicted_j_error_type)
        reg.calculate()
        return reg

# ============= EOF =============================================
