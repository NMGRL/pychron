# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
import math

from numpy import array, nan
from traits.api import HasTraits, List, Property, cached_property, Str, Bool, Int, Event, Float
from uncertainties import ufloat, nominal_value, std_dev

from pychron.core.stats.core import calculate_mswd, calculate_weighted_mean, validate_mswd
from pychron.processing.argon_calculations import calculate_plateau_age, age_equation, calculate_isochron
from pychron.pychron_constants import ALPHAS, AGE_MA_SCALARS, MSEM, SD


def AGProperty(*depends):
    d = 'dirty,analyses:[status,temp_status]'
    # d = 'dirty'  # ,analyses:[status,temp_status]'
    if depends:
        d = '{},{}'.format(','.join(depends), d)

    return Property(depends_on=d)


class AnalysisGroup(HasTraits):
    attribute = Str('uage')
    analyses = List
    nanalyses = AGProperty()

    arith_age = AGProperty()
    arith_age_error_kind = Str

    # arith_age_error_kind = Enum(*ERROR_TYPES)

    weighted_age = AGProperty()
    # weighted_age_error_kind = Enum(*ERROR_TYPES)
    weighted_age_error_kind = Str  # Enum(*ERROR_TYPES)

    weighted_kca = AGProperty()
    arith_kca = AGProperty()

    mswd = Property

    isochron_age = AGProperty()
    isochron_age_error_kind = Str
    identifier = Property

    repository_identifier = Property(depends_on='_repository_identifier')
    _repository_identifier = Str

    irradiation = Property
    irradiation_label = Property
    sample = Property
    aliquot = Property
    material = Property
    unit = Str
    location = Str

    _sample = Str
    age_scalar = Property
    age_units = Property

    j_err = AGProperty()
    include_j_error_in_mean = Bool(True)
    include_j_error_in_individual_analyses = Bool(False)

    percent_39Ar = AGProperty()
    dirty = Event

    total_n = AGProperty()

    def get_mswd_tuple(self):
        mswd = self.mswd
        valid_mswd = validate_mswd(mswd, self.nanalyses)
        return mswd, valid_mswd, self.nanalyses

    def _get_age_units(self):
        return self.analyses[0].arar_constants.age_units

    def _get_age_scalar(self):
        au = self.age_units
        return AGE_MA_SCALARS[au]

    # @cached_property
    def _get_mswd(self):
        attr = self.attribute
        if attr.startswith('uage'):
            attr = 'uage'
            if self.include_j_error_in_individual_analyses:
                attr = 'uage_w_j_err'

        return self._calculate_mswd(attr)

    def _calculate_mswd(self, attr):
        m = 0
        args = self._get_values(attr)
        if args:
            vs, es = args
            m = calculate_mswd(vs, es)

        return m

    @cached_property
    def _get_j_err(self):
        j = self.analyses[0].j
        try:
            e = (j.std_dev / j.nominal_value) if j is not None else 0
        except ZeroDivisionError:
            e = nan
        return e

    @cached_property
    def _get_isochron_age(self):
        return self._calculate_isochron_age()

    @cached_property
    def _get_aliquot(self):
        return self.analyses[0].aliquot

    @cached_property
    def _get_identifier(self):
        return self.analyses[0].labnumber

    @cached_property
    def _get_repository_identifier(self):
        if self._repository_identifier:
            return self._repository_identifier
        else:
            return self.analyses[0].repository_identifier

    def _set_repository_identifier(self, v):
        self._repository_identifier = v

    @cached_property
    def _get_irradiation_label(self):
        return self.analyses[0].irradiation_label

    @cached_property
    def _get_irradiation(self):
        return self.analyses[0].irradiation

    @cached_property
    def _get_material(self):
        return self.analyses[0].material

    @cached_property
    def _get_sample(self):
        sam = self._sample
        if not sam:
            sam = self.analyses[0].sample
        return sam

    def _set_sample(self, s):
        self._sample = s

    @cached_property
    def _get_percent_39Ar(self):
        return 0

    # @cached_property
    def _get_weighted_age(self):
        attr = self.attribute
        if attr.startswith('uage'):
            attr = 'uage_w_j_err' if self.include_j_error_in_individual_analyses else 'uage'
        # if self.include_j_error_in_individual_analyses:
        #         v, e = self._calculate_weighted_mean('uage', self.weighted_age_error_kind)
        #     else:
        #         v, e = self._calculate_weighted_mean('uage_wo_j_err', self.weighted_age_error_kind)
        # else:
        v, e = self._calculate_weighted_mean(attr, self.weighted_age_error_kind)
        e = self._modify_error(v, e, self.weighted_age_error_kind)
        try:
            return ufloat(v, max(0, e))
        except AttributeError:
            return ufloat(0, 0)

    def _modify_error(self, v, e, kind, mswd=None, include_j_error=None):

        if mswd is None:
            mswd = self.mswd

        if kind == MSEM:
            e *= mswd ** 0.5 if mswd > 1 else 1

        if 'age' in self.attribute:
            if include_j_error is None:
                include_j_error = self.include_j_error_in_mean

            if include_j_error:
                try:
                    e = ((e / v) ** 2 + self.j_err ** 2) ** 0.5 * v
                except ZeroDivisionError:
                    return nan
        return e

    # @cached_property
    def _get_weighted_kca(self):
        return ufloat(*self._calculate_weighted_mean('kca'))

    # @cached_property
    def _get_arith_kca(self):
        return ufloat(*self._calculate_arithmetic_mean('kca'))

    # @cached_property
    def _get_arith_age(self):
        if self.include_j_error_in_individual_analyses:
            v, e = self._calculate_arithmetic_mean('uage')
        else:
            v, e = self._calculate_arithmetic_mean('uage_wo_j_err')
        e = self._modify_error(v, e, self.arith_age_error_kind)
        return ufloat(v, e)

    @cached_property
    def _get_total_n(self):
        return len(self.analyses)

    @cached_property
    def _get_nanalyses(self):
        return len(list(self.clean_analyses()))

    def clean_analyses(self):
        return (ai for ai in self.analyses if not ai.is_omitted())

    def _get_values(self, attr):
        vs = (getattr(ai, attr) for ai in self.clean_analyses())
        vs = [vi for vi in vs if vi is not None]
        if vs:
            vs, es = zip(*[(nominal_value(v), std_dev(v)) for v in vs])
            vs, es = array(vs), array(es)
            return vs, es

    def _calculate_mean(self, attr, use_weights=True, error_kind=None):
        args = self._get_values(attr)
        if args:
            vs, es = args
            if use_weights:
                av, werr = calculate_weighted_mean(vs, es)
                if error_kind == SD:
                    n = len(vs)
                    werr = (sum((av - vs) ** 2) / (n - 1)) ** 0.5

            else:
                av = vs.mean()
                werr = vs.std(ddof=1)
        else:
            av, werr = 0, 0

        return av, werr

    def _calculate_arithmetic_mean(self, attr):
        return self._calculate_mean(attr, use_weights=False)

    def _calculate_weighted_mean(self, attr, error_kind=None):
        return self._calculate_mean(attr, use_weights=True, error_kind=error_kind)

    def get_isochron_data(self):
        return calculate_isochron(list(self.clean_analyses()), self.isochron_age_error_kind)

    def _calculate_isochron_age(self):
        args = calculate_isochron(list(self.clean_analyses()), self.isochron_age_error_kind)
        if args:
            age = args[0]
            reg = args[1]
            v, e = age.nominal_value, age.std_dev
            e = self._modify_error(v, e, self.isochron_age_error_kind,
                                   mswd=reg.mswd)

            return ufloat(v, e)


class StepHeatAnalysisGroup(AnalysisGroup):
    plateau_age = AGProperty()
    integrated_age = AGProperty()

    include_j_error_in_plateau = Bool(True)
    plateau_steps_str = Str
    plateau_steps = None

    plateau_age_error_kind = Str
    nsteps = Int
    fixed_step_low = Str
    fixed_step_high = Str

    plateau_nsteps = Int(3)
    plateau_gas_fraction = Float(50)
    plateau_mswd = Float
    plateau_mswd_valid = Bool
    # def _get_nanalyses(self):
    #     if self.plateau_steps:
    #         n = self.nsteps
    #     else:
    #         n = super(StepHeatAnalysisGroup, self)._get_nanalyses()
    #     return n

    def get_plateau_mswd_tuple(self):
        return self.plateau_mswd, self.plateau_mswd_valid, self.nsteps

    def calculate_plateau(self):
        return self.plateau_age

    @cached_property
    def _get_integrated_age(self):
        rad40, k39 = zip(*[(a.get_computed_value('rad40'),
                            a.get_computed_value('k39')) for a in self.clean_analyses()])
        rad40 = sum(rad40)
        k39 = sum(k39)

        j = a.j
        try:
            return age_equation(rad40 / k39, j, a.arar_constants)
        except ZeroDivisionError:
            return nan

    # def _get_steps(self):
    #     d = [(ai.age,
    #           ai.age_err,
    #           nominal_value(ai.get_computed_value('k39')))
    #          for ai in self.clean_analyses()]
    #
    #     return zip(*d)

    @property
    def fixed_steps(self):
        l, h = '', ''
        if self.fixed_step_low:
            l = self.fixed_step_low

        if self.fixed_step_high:
            h = self.fixed_step_high

        if not (l is None and h is None):
            return l, h

    # @cached_property
    def _get_plateau_age(self):
        # ages, errors, k39 = self._get_steps()

        ages = [ai.age for ai in self.analyses]
        errors = [ai.age_err for ai in self.analyses]
        k39 = [nominal_value(ai.get_computed_value('k39')) for ai in self.analyses]

        options = {'nsteps': self.plateau_nsteps,
                   'gas_fraction': self.plateau_gas_fraction,
                   'fixed_steps': self.fixed_steps}

        excludes = [i for i in enumerate(self.analyses) if ai.is_omitted()]
        args = calculate_plateau_age(ages, errors, k39, options=options, excludes=excludes)
        if args:
            v, e, pidx = args
            if pidx[0] == pidx[1]:
                return

            self.plateau_steps = pidx
            self.plateau_steps_str = '{}-{}'.format(ALPHAS[pidx[0]],
                                                    ALPHAS[pidx[1]])

            step_idxs = [i for i in xrange(pidx[0], pidx[1] + 1) if not self.analyses[i].is_omitted()]
            self.nsteps = len(step_idxs)

            pages = [ages[i] for i in step_idxs]
            perrs = [errors[i] for i in step_idxs]

            mswd = calculate_mswd(pages, perrs)
            self.plateau_mswd_valid = validate_mswd(mswd, self.nsteps)
            self.plateau_mswd = mswd

            e = self._modify_error(v, e,
                                   self.plateau_age_error_kind,
                                   mswd=mswd,
                                   include_j_error=self.include_j_error_in_plateau)
            if math.isnan(e):
                e = 0

            return ufloat(v, max(0, e))


class InterpretedAgeGroup(StepHeatAnalysisGroup):
    uuid = Str
    all_analyses = List
    preferred_age = Property(depends_on='preferred_age_kind')
    preferred_age_value = Property(depends_on='preferred_age_kind')
    preferred_age_error = Property(depends_on='preferred_age_kind, preferred_age_error_kind')
    preferred_mswd = Property(depends_on='preferred_age_kind')

    preferred_kca = Property(depends_on='preferred_kca_kind')
    preferred_kca_value = Property(depends_on='preferred_kca_kind')
    preferred_kca_error = Property(depends_on='preferred_kca_kind')

    preferred_age_kind = Str('Weighted Mean')
    preferred_kca_kind = Str('Weighted Mean')

    preferred_age_error_kind = Str(MSEM)  # ('SD')
    preferred_ages = Property(depends_on='analyses')

    name = Str
    use = Bool

    def _get_nanalyses(self):
        if self.preferred_age_kind == 'Plateau':
            return self.nsteps
        else:
            return super(InterpretedAgeGroup, self)._get_nanalyses()

    def _preferred_age_error_kind_changed(self, new):
        self.weighted_age_error_kind = new
        self.arith_age_error_kind = new
        self.plateau_age_error_kind = new
        self.isochron_age_error_kind = new

    def get_is_plateau_step(self, an):
        plateau_step = False
        if self.preferred_age_kind == 'Plateau':
            if self.plateau_age:
                if not an.is_omitted():
                    idx = self.analyses.index(an)
                    ps, pe = self.plateau_steps

                    plateau_step = ps <= idx <= pe

        return plateau_step

    def get_ma_scaled_age(self):
        a = self.preferred_age
        return a * self.age_scalar

    def _get_preferred_mswd(self):
        if self.preferred_age_kind == 'Plateau':
            return self.plateau_mswd
        else:
            return self.mswd

    def _get_preferred_age_value(self):
        pa = self.preferred_age
        v = 0
        if pa is not None:
            v = float(nominal_value(pa))
        return v

    def _get_preferred_age_error(self):
        pa = self.preferred_age
        e = 0
        if pa is not None:
            e = float(std_dev(pa))
        return e

    def _get_preferred_kca_value(self):
        pa = self.preferred_kca
        v = 0
        if pa is not None:
            v = float(nominal_value(pa))
        return v

    def _get_preferred_kca_error(self):
        pa = self.preferred_kca
        e = 0
        if pa is not None:
            e = float(std_dev(pa))
        return e

    def _get_preferred_kca(self):
        if self.preferred_kca_kind == 'Weighted Mean':
            pa = self.weighted_kca
        else:
            pa = self.arith_kca
        return pa

    def _get_preferred_age(self):
        pa = None
        if self.preferred_age_kind == 'Weighted Mean':
            pa = self.weighted_age
        elif self.preferred_age_kind == 'Arithmetic Mean':
            pa = self.arith_age
        elif self.preferred_age_kind == 'Isochron':
            pa = self.isochron_age
        elif self.preferred_age_kind == 'Integrated':
            pa = self.integrated_age
        elif self.preferred_age_kind == 'Plateau':
            pa = self.plateau_age

        return pa

    @cached_property
    def _get_preferred_ages(self):
        ps = ['Weighted Mean', 'Arithmetic Mean', 'Isochron',
              'Integrated', 'Plateau']
        # if self.analyses:
        #     ref = self.analyses[0]
        #     print 'asfasfasdfasfas', ref, ref.step
        #     if ref.step:
        #         ps.append('Integrated')
        #         if self.plateau_age:
        #             ps.append('Plateau')

        return ps

# ============= EOF =============================================

# class AnalysisRatioMean(AnalysisGroup):
#    Ar40_39 = Property
#    Ar37_39 = Property
#    Ar36_39 = Property
#    kca = Property
#    kcl = Property
#
#    def _get_Ar40_39(self):
#        return self._calculate_weighted_mean('Ar40_39')
#
#    #        return self._calculate_weighted_mean('rad40') / self._calculate_weighted_mean('k39')
#
#    def _get_Ar37_39(self):
#        return self._calculate_weighted_mean('Ar37_39')
#
#    #        return self._calculate_weighted_mean('Ar37') / self._calculate_weighted_mean('Ar39')
#
#    def _get_Ar36_39(self):
#        return self._calculate_weighted_mean('Ar36_39')
#
#    #        return self._calculate_weighted_mean('Ar36') / self._calculate_weighted_mean('Ar39')
#
#    def _get_kca(self):
#        return self._calculate_weighted_mean('kca')
#
#    def _get_kcl(self):
#        return self._calculate_weighted_mean('kcl')
#
# class AnalysisIntensityMean(AnalysisGroup):
#    Ar40 = Property
#    Ar39 = Property
#    Ar38 = Property
#    Ar37 = Property
#    Ar36 = Property
#
#    def _get_Ar40(self):
#        return self._calculate_weighted_mean('Ar40')
#
#    def _get_Ar39(self):
#        return self._calculate_weighted_mean('Ar39')
#
#    def _get_Ar38(self):
#        return self._calculate_weighted_mean('Ar38')
#
#    def _get_Ar37(self):
#        return self._calculate_weighted_mean('Ar37')
#
#    def _get_Ar36(self):
#        return self._calculate_weighted_mean('Ar36')
