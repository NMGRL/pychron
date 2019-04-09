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


import math

from numpy import array, nan, average
# ============= enthought library imports =======================
from traits.api import List, Property, cached_property, Str, Bool, Int, Event, Float, Any, Enum, on_trait_change
from uncertainties import ufloat, nominal_value, std_dev

from pychron.core.stats.core import calculate_mswd, calculate_weighted_mean, validate_mswd
from pychron.experiment.utilities.identifier import make_aliquot
from pychron.processing.analyses.analysis import IdeogramPlotable
from pychron.processing.analyses.preferred import Preferred
from pychron.processing.arar_age import ArArAge
from pychron.processing.argon_calculations import calculate_plateau_age, age_equation, calculate_isochron
from pychron.pychron_constants import ALPHAS, MSEM, SD, SUBGROUPING_ATTRS, ERROR_TYPES, WEIGHTED_MEAN, \
    DEFAULT_INTEGRATED, SUBGROUPINGS, ARITHMETIC_MEAN, PLATEAU_ELSE_WEIGHTED_MEAN, WEIGHTINGS, FLECK, NULL_STR


def AGProperty(*depends):
    d = 'dirty,analyses:[temp_status]'
    if depends:
        d = '{},{}'.format(','.join(depends), d)

    return Property(depends_on=d)


def MetaDataProperty(*depends):
    d = 'metadata_refresh_needed'
    if depends:
        d = '{},{}'.format(','.join(depends), d)

    return Property(depends_on=d)


class AnalysisGroup(IdeogramPlotable):
    attribute = Str('uage')
    analyses = List
    nanalyses = AGProperty()
    age_span = AGProperty()

    weighted_age = AGProperty()
    arith_age = AGProperty()
    integrated_age = AGProperty()
    isochron_age = AGProperty()
    j_err = AGProperty()
    j = AGProperty()
    total_n = AGProperty()

    integrated_age_weighting = Enum(WEIGHTINGS)
    include_j_error_in_integrated = Bool(False)

    age_error_kind = Enum(*ERROR_TYPES)
    kca_error_kind = Enum(*ERROR_TYPES)
    kcl_error_kind = Enum(*ERROR_TYPES)
    rad40_error_kind = Enum(*ERROR_TYPES)
    moles_k39_error_kind = Enum(*ERROR_TYPES)
    signal_k39_error_kind = Enum(*ERROR_TYPES)

    mswd = Property

    isochron_age_error_kind = Str

    identifier = Any
    aliquot = Any
    repository_identifier = Any
    irradiation = Any
    irradiation_level = Any
    irradiation_position = Any
    sample = Any
    project = Any
    material = Any
    igsn = Any
    lithology = Any
    lithology_type = Any
    lithology_group = Any
    lithology_class = Any
    latitude = Any
    longitude = Any
    reference = Any
    rlocation = Any

    arar_constants = Any
    production_ratios = Any
    monitor_info = Any
    monitor_age = Any
    monitor_reference = Any
    age_units = Any
    grainsize = Any

    unit = Str
    location = Str

    # age_scalar = Property
    # age_units = AGProperty()

    include_j_error_in_mean = Bool(True)
    include_j_position_error = Bool(False)

    # percent_39Ar = AGProperty()
    dirty = Event

    isochron_4036 = None
    isochron_regressor = None

    def __init__(self, *args, **kw):
        super(AnalysisGroup, self).__init__(make_arar_constants=False, *args, **kw)

    def _analyses_changed(self, new):
        if new:
            a = new[0]
            for attr in ('identifier',
                         'aliquot',
                         'repository_identifier',
                         'igsn',
                         'sample',
                         'material',
                         'grainsize',
                         'project',
                         'irradiation',
                         'irradiation_position',
                         'irradiation_level',
                         'irradiation_label',
                         'unit',
                         'lithology',
                         'lithology_type',
                         'lithology_group',
                         'lithology_class',
                         'latitude',
                         'longitude',
                         'reference',
                         'rlocation',
                         'production_ratios',
                         'arar_constants',
                         'monitor_age',
                         'monitor_reference'):
                try:
                    setattr(self, attr, getattr(a, attr))
                except AttributeError:
                    pass

            try:
                self.monitor_info = a.monitor_age, a.monitor_reference
            except AttributeError:
                pass

            self.age_units = self.arar_constants.age_units

    def attr_stats(self, attr):
        w, sd, sem, (vs, es) = self._calculate_weighted_mean(attr, error_kind='both')
        mswd = calculate_mswd(vs, es, wm=w)
        valid_mswd = validate_mswd(mswd, self.nanalyses)
        mi = min(vs)
        ma = max(vs)

        total_dev = (ma - mi) / ma * 100

        return {'mean': w,
                'sd': sd,
                'sem': sem,
                'mswd': mswd,
                'valid_mswd': valid_mswd,
                'min': mi, 'max': ma, 'total_dev': total_dev}

    def get_mswd_tuple(self):
        mswd = self.mswd
        valid_mswd = validate_mswd(mswd, self.nanalyses)
        return mswd, valid_mswd, self.nanalyses

    def set_j_error(self, individual, mean, dirty=False):
        self.include_j_position_error = individual
        self.include_j_error_in_mean = mean

        if dirty:
            self.dirty = True

    def get_arithmetic_mean(self, *args, **kw):
        return self._calculate_arithmetic_mean(*args, **kw)

    def get_weighted_mean(self, *args, **kw):
        return self._get_weighted_mean(*args, **kw)

    def plateau_analyses(self):
        return

    def clean_analyses(self):
        return (ai for ai in self.analyses if not ai.is_omitted())

    def get_isochron_data(self):
        ans = [a for a in self.analyses if isinstance(a, ArArAge)]
        exclude = [i for i, x in enumerate(ans) if x.is_omitted()]
        if ans:
            return calculate_isochron(ans, self.isochron_age_error_kind, exclude=exclude)

    def calculate_isochron_age(self):
        args = self.get_isochron_data()
        if args:
            age = args[0]
            self.isochron_4036 = args[1]
            reg = args[2]
            self.isochron_regressor = reg
            v, e = nominal_value(age), std_dev(age)
            e = self._modify_error(v, e, self.isochron_age_error_kind, mswd=reg.mswd)

            return ufloat(v, e)

    def isochron_mswd(self):
        if not self.isochron_4036:
            self.calculate_isochron_age()
        reg = self.isochron_regressor

        return reg.mswd, reg.valid_mswd, reg.n

    # properties
    @property
    def nratio(self):
        return '{}/{}'.format(self.nanalyses, len(self.analyses))

    @property
    def labnumber(self):
        return self.identifier

    @property
    def age_attr(self):
        return 'uage_w_position_err' if self.include_j_position_error else 'uage'

    def _get_mswd(self):
        attr = self.attribute
        if attr.startswith('uage'):
            attr = 'uage'
            if self.include_j_position_error:
                attr = 'uage_w_position_err'

        return self._calculate_mswd(attr)

    @cached_property
    def _get_age_span(self):
        ans = self.clean_analyses()
        ages = [nominal_value(a.age) for a in ans]
        return max(ages) - min(ages)

    @cached_property
    def _get_j_err(self):
        j = self.j
        try:
            e = (std_dev(j) / nominal_value(j)) if j is not None else 0
        except ZeroDivisionError:
            e = nan
        return e

    @cached_property
    def _get_j(self):
        j = ufloat(0, 0)
        if self.analyses:
            j = self.analyses[0].j
        return j

    @cached_property
    def _get_isochron_age(self):
        a = self.calculate_isochron_age()
        if a is None:
            a = ufloat(0, 0)

        return a

    @cached_property
    def _get_arith_age(self):
        v, e = self._calculate_arithmetic_mean(self.age_attr)
        e = self._modify_error(v, e, self.age_error_kind)
        aa = ufloat(v, e)
        return self._apply_j_err(aa)

    @cached_property
    def _get_weighted_age(self):
        attr = self.attribute
        if attr.startswith('uage'):
            attr = self.age_attr

        v, e = self._calculate_weighted_mean(attr, self.age_error_kind)
        me = self._modify_error(v, e, self.age_error_kind)
        try:
            wa = ufloat(v, max(0, me))
            return self._apply_j_err(wa)

        except AttributeError:
            return ufloat(0, 0)

    @cached_property
    def _get_total_n(self):
        return len(self.analyses)

    @cached_property
    def _get_nanalyses(self):
        return len(list(self.clean_analyses()))

    # private functions
    def _calculate_mswd(self, attr, values=None):
        m = 0
        if values is None:
            values = self._get_values(attr)
        if values:
            vs, es = values
            m = calculate_mswd(vs, es)

        return m

    def _apply_j_err(self, wa, force=False):
        if self.include_j_error_in_mean or force:
            v, e = nominal_value(wa), std_dev(wa)
            v = abs(v)
            try:
                pa = e / v
            except ZeroDivisionError:
                pa = 0

            pj = self.j_err

            ne = (pa ** 2 + pj ** 2) ** 0.5
            wa = ufloat(v, ne * v)

        return wa

    def _modify_error(self, v, e, kind, mswd=None):

        if mswd is None:
            mswd = self.mswd

        if kind == MSEM:
            e *= mswd ** 0.5 if mswd > 1 else 1

        return e

    def _get_weighted_mean(self, attr, kind=None):
        if attr == 'age':
            return self.weighted_age

        if kind is None:
            kind = getattr(self, '{}_error_kind'.format(attr), SD)
        v, e = self._calculate_weighted_mean(attr, error_kind=kind)
        mswd = self._calculate_mswd(attr)
        e = self._modify_error(v, e, kind, mswd)
        return ufloat(v, e)

    def _get_values(self, attr):
        vs = (ai.get_value(attr) for ai in self.clean_analyses())
        ans = [vi for vi in vs if vi is not None]
        if ans:
            vs = [nominal_value(v) for v in ans]
            es = [std_dev(v) for v in ans]
            return array(vs), array(es)

    def _calculate_mean(self, attr, use_weights=True, error_kind=None):
        def sd(a, v, e):
            n = len(v)
            if n == 1:
                we = e[0]
            else:
                we = (sum((a - v) ** 2) / (n - 1)) ** 0.5
            return we

        args = self._get_values(attr)
        sem = 0
        if args:
            vs, es = args
            if use_weights:
                av, werr = calculate_weighted_mean(vs, es)

                if error_kind == 'both':
                    sem = werr
                    werr = sd(av, vs, es)

                elif error_kind == SD:
                    werr = sd(av, vs, es)

            else:
                av = vs.mean()
                werr = vs.std(ddof=1)
        else:
            av, werr = 0, 0

        if error_kind == 'both':
            return av, werr, sem, args
        else:
            return av, werr

    def _calculate_integrated_mean_error(self, weighting, ks, rs):
        sks = ks.sum()
        weights = None

        fs = rs / ks
        errors = array([std_dev(f) for f in fs])
        values = array([nominal_value(f) for f in fs])
        if weighting == 'Volume':
            vpercent = ks / sks
            weights = [nominal_value(wi) for wi in (vpercent * errors) ** 2]
        elif weighting == 'Variance':
            weights = 1 / errors ** 2

        if weights is not None:
            wmean, sum_weights = average(values, weights=weights, returned=True)
            if weighting == 'Volume':
                werr = sum_weights ** 0.5
            else:
                werr = sum_weights ** -0.5

            f = ufloat(wmean, werr)
        else:
            f = rs.sum()/sks

        return f

    def _calculate_integrated(self, attr, kind='total', weighting=None):

        uv = ufloat(0, 0)
        if kind == 'total':
            ans = self.analyses
        elif kind == 'valid':
            ans = list(self.clean_analyses())
        elif kind == 'plateau':
            ans = list(self.plateau_analyses())

        ans = [a for a in ans if not isinstance(a, InterpretedAgeGroup)]
        if ans:

            prs = ans[0].production_ratios

            def apply_pr(r, k):
                pr = 1
                if prs:
                    pr = prs.get(k, 1)
                    if not pr:
                        pr = 1.0

                    # pr = 1 / pr

                v = r * pr

                return v

            if attr in ('kca', 'kcl', 'signal_k39'):
                ks = array([ai.get_computed_value('k39') for ai in ans])

                if attr == 'kca':
                    cas = array([ai.get_non_ar_isotope('ca37') for ai in ans])
                    f = self._calculate_integrated_mean_error(weighting, ks, cas)
                    uv = 1/apply_pr(f, 'Ca_K')

                elif attr == 'kcl':
                    cls = array([ai.get_non_ar_isotope('cl38') for ai in ans])
                    f = self._calculate_integrated_mean_error(weighting, ks, cls)
                    uv = 1/apply_pr(f, 'Cl_K')

                elif attr == 'signal_k39':
                    uv = ks.sum()

            elif attr == 'radiogenic_yield':
                ns = [ai.rad40 for ai in ans]
                ds = [ai.total40 for ai in ans]
                uv = sum(ns) / sum(ds) * 100
            elif attr == 'moles_k39':
                uv = sum([ai.moles_k39 for ai in ans])
            elif attr == 'age':
                uv = self._calculate_integrated_age(ans, weighting)

        return uv

    def _calculate_arithmetic_mean(self, attr):
        if attr == 'age':
            return self.arith_age

        return self._calculate_mean(attr, use_weights=False)

    def _calculate_weighted_mean(self, attr, error_kind=None):
        return self._calculate_mean(attr, use_weights=True, error_kind=error_kind)

    def _calculate_integrated_age(self, ans, weighting=None):
        ret = ufloat(0, 0)
        if ans and all((not isinstance(a, InterpretedAgeGroup) for a in ans)):

            rs = array([a.get_computed_value('rad40') for a in ans])
            ks = array([a.get_computed_value('k39') for a in ans])

            # sks = ks.sum()
            # fs = rs / ks
            if weighting is None:
                weighting = self.integrated_age_weighting

            # if weighting == 'Volume':
            #     vpercent = array([nominal_value(v) for v in ks / sks])
            #     errs = array([std_dev(f) for f in fs])
            #     weights = (vpercent * errs) ** 2
            #
            # elif weighting == 'Variance':
            #     weights = [std_dev(f) ** -2 for f in fs]
            #
            # if weights is not None:
            #     wmean, sum_weights = average([nominal_value(fi) for fi in fs], weights=weights, returned=True)
            #     if weighting == 'Volume':
            #         werr = sum_weights ** 0.5
            #     else:
            #         werr = sum_weights ** -0.5
            #
            #     f = ufloat(wmean, werr)
            # else:
            #     f = rs.sum() / sks
            f = self._calculate_integrated_mean_error(weighting, ks, rs)

            j = self.j
            if not self.include_j_error_in_integrated:
                j = nominal_value(j)

            try:
                ret = age_equation(f, j, arar_constants=self.arar_constants)
            except ZeroDivisionError:
                pass

        return ret


class StepHeatAnalysisGroup(AnalysisGroup):
    plateau_age = AGProperty()
    integrated_age = AGProperty()

    integrated_include_omitted = Bool(False)
    include_j_error_in_plateau = Bool(True)
    plateau_steps_str = Str
    plateau_steps = None

    nsteps = Int
    fixed_step_low = Str
    fixed_step_high = Str
    plateau_age_error_kind = Str

    plateau_nsteps = Int(3)
    plateau_gas_fraction = Float(50)
    plateau_overlap_sigma = Int(2)
    plateau_mswd = Float
    plateau_mswd_valid = Bool
    plateau_method = Str(FLECK)

    total_ar39 = AGProperty()
    total_k2o = AGProperty()

    def set_isochron_trapped(self, state, include_error=None):
        v = None
        if state:
            self.calculate_isochron_age()
            v = 1 / self.isochron_4036
            if not include_error:
                v = ufloat(nominal_value(v), std_dev=0)

        for a in self.analyses:
            a.arar_constants.trapped_atm4036 = v
            a.recalculate_age(force=True)

    @property
    def integrated_enabled(self):
        """
        see issue 1565.

         Total integrated age only appropriate for single-aliquot groups or subgroups
        :return:
        """

        return self.nanalyses > 1 and len({a.aliquot for a in self.analyses}) == 1

    def plateau_analyses(self):
        return [a for a in self.clean_analyses() if self.get_is_plateau_step(a)]

    @cached_property
    def _get_total_k2o(self):
        total = sum([a.total_k2o if isinstance(a, StepHeatAnalysisGroup) else a.k2o for a in self.analyses])
        return nominal_value(total)

    @cached_property
    def _get_total_ar39(self):
        total = sum([a.get_computed_value('k39') for a in self.analyses])
        return nominal_value(total)

    def plateau_total_ar39(self):
        ptotal = sum([a.get_computed_value('k39') for a in self.plateau_analyses()])
        return nominal_value(ptotal / self.total_ar39 * 100)

    def valid_total_ar39(self):
        cleantotal = sum([a.get_computed_value('k39') for a in self.clean_analyses()])
        return nominal_value(cleantotal / self.total_ar39 * 100)

    def cumulative_ar39(self, idx):
        cum = 0
        for i, a in enumerate(self.analyses):
            if i > idx:
                break
            cum += a.get_computed_value('k39')

        return nominal_value(cum / self.total_ar39 * 100)

    def get_plateau_mswd_tuple(self):
        return self.plateau_mswd, self.plateau_mswd_valid, self.nsteps

    def calculate_plateau(self):
        return self.plateau_age

    def get_is_plateau_step(self, an):
        if isinstance(an, int):
            idx = an
            an = self.analyses[idx]
        else:
            idx = self.analyses.index(an)

        plateau_step = False
        if self.plateau_steps:
            if not an.is_omitted():
                ps, pe = self.plateau_steps
                plateau_step = ps <= idx <= pe

        return plateau_step

    @cached_property
    def _get_integrated_age(self):
        if self.integrated_include_omitted:
            ans = self.analyses
        else:
            ans = list(self.clean_analyses())
        return self._calculate_integrated_age(ans)

    @property
    def fixed_steps(self):
        l, h = '', ''
        if self.fixed_step_low:
            l = self.fixed_step_low

        if self.fixed_step_high:
            h = self.fixed_step_high

        if not (l is None and h is None):
            return l, h

    @cached_property
    def _get_plateau_age(self):
        ans = self.analyses
        v, e = 0, 0
        if all((not isinstance(ai, InterpretedAgeGroup) for ai in ans)):
            if ans:
                ages = [ai.age for ai in ans]
                errors = [ai.age_err for ai in ans]

                k39 = [nominal_value(ai.get_computed_value('k39')) for ai in ans]

                options = {'nsteps': self.plateau_nsteps,
                           'gas_fraction': self.plateau_gas_fraction,
                           'overlap_sigma': self.plateau_overlap_sigma,
                           'fixed_steps': self.fixed_steps}

                excludes = [i for i, ai in enumerate(ans) if ai.is_omitted()]
                args = calculate_plateau_age(ages, errors, k39, method=self.plateau_method,
                                             options=options, excludes=excludes)

                if args:
                    v, e, pidx = args
                    if pidx[0] == pidx[1]:
                        return
                    self.plateau_steps = pidx
                    self.plateau_steps_str = '{}-{}'.format(ALPHAS[pidx[0]],
                                                            ALPHAS[pidx[1]])

                    step_idxs = [i for i in range(pidx[0], pidx[1] + 1) if not ans[i].is_omitted()]
                    self.nsteps = len(step_idxs)

                    pages = array([ages[i] for i in step_idxs])
                    perrs = array([errors[i] for i in step_idxs])

                    mswd = calculate_mswd(pages, perrs)
                    self.plateau_mswd_valid = validate_mswd(mswd, self.nsteps)
                    self.plateau_mswd = mswd
                    if self.plateau_age_error_kind == SD:
                        e = array(pages).std()
                    else:
                        e = self._modify_error(v, e,
                                               self.plateau_age_error_kind,
                                               mswd=mswd)
                    if math.isnan(e):
                        e = 0

        a = ufloat(v, max(0, e))
        self._apply_j_err(a, force=self.include_j_error_in_mean or self.include_j_error_in_plateau)

        return a


class InterpretedAgeGroup(StepHeatAnalysisGroup, Preferred):
    uuid = Str
    all_analyses = List
    subgroup_id = Int
    # preferred_values = List

    name = Str
    use = Bool

    lithology_classes = List
    lithology_groups = List
    lithology_types = List
    lithologies = List

    comments = Str
    preferred_age = Property

    # modeled_j = ''
    # modeled_j_err = ''
    # F = ''
    # F_err = ''
    # rundate = ''

    def __init__(self, *args, **kw):
        super(InterpretedAgeGroup, self).__init__(*args, **kw)
        super(Preferred, self).__init__()
        if self.analyses:
            self.has_subgroups(self.analyses)

    def set_preferred_age(self, pk, ek):
        pv = self._get_pv('age')
        pv.error_kind = ek
        pv.kind = pk
        pv.dirty = True

    def ages(self, asfloat=True):
        vs = {k: getattr(self, k) for k in ('weighted_age', 'plateau_age', 'isochron_age', 'integrated_age')}
        if asfloat:
            es = {}
            for k, v in vs.items():
                vs[k] = nominal_value(v)
                es['{}_err'.format(k)] = std_dev(v)

            vs.update(es)
        return vs

    @property
    def age(self):
        return self.preferred_age

    @property
    def uage(self):
        return self.age

    @property
    def uage_w_j_err(self):
        return self.age

    @property
    def uage_w_position_err(self):
        return self.age

    @property
    def kca(self):
        pv = self._get_pv('kca')
        return pv.uvalue

    @property
    def kcl(self):
        pv = self._get_pv('kcl')
        return pv.uvalue

    @property
    def radiogenic_yield(self):
        pv = self._get_pv('radiogenic_yield')
        return pv.uvalue

    @property
    def moles_k39(self):
        pv = self._get_pv('moles_k39')
        return pv.uvalue

    @property
    def k39(self):
        return self.signal_k39

    @property
    def signal_k39(self):
        pv = self._get_pv('signal_k39')
        return pv.uvalue

    def get_value(self, attr):
        if hasattr(self, attr):
            ret = getattr(self, attr)
        else:
            ret = ufloat(0, 0)
        return ret

    @on_trait_change('analyses')
    def has_subgroups(self, new):
        hs = any((isinstance(a, InterpretedAgeGroup) for a in new))
        for pv in self.preferred_values:
            if pv.attr == 'age':
                continue

            if hs:
                if pv.attr in ('kca', 'kcl', 'moles_k39', 'signal_k39'):
                    pv.kind = ARITHMETIC_MEAN
                else:
                    pv.kind = WEIGHTED_MEAN

                pv.kinds = [WEIGHTED_MEAN, ARITHMETIC_MEAN]
            else:
                pv.kinds = SUBGROUPINGS

    @on_trait_change('preferred_values:[kind, error_kind, dirty, weighting]')
    def handle_preferred_change(self, obj, name, old, new):
        if obj.attr == 'age':
            if 'Plateau' in obj.kind:
                self.plateau_age_error_kind = obj.error_kind
                if obj.kind != 'Plateau':
                    self.age_error_kind = obj.error_kind
            else:
                self.age_error_kind = obj.error_kind

            self.dirty = True
            v = self._get_preferred_age()
            obj.value = nominal_value(v)
            obj.error = std_dev(v)
            self.dirty = True
        else:
            v, k = self._get_preferred_(obj.attr, obj.kind, obj.error_kind, obj.weighting)
            obj.value = nominal_value(v)
            obj.error = std_dev(v)
            obj.computed_kind = k

    def preferred_values_to_dict(self):
        return [pv.to_dict() for pv in self.preferred_values]

    def get_preferred_age(self):
        return self._get_preferred_age()

    def get_ma_scaled_age(self):
        a = self._get_preferred_age()
        return self.arar_constants.scale_age(a, 'Ma')

    def scaled_age(self, a, units='Ma'):
        return self.arar_constants.scale_age(a, units)

    def get_preferred_mswd(self):
        pv = self._get_pv('age')
        if pv.computed_kind.lower() == 'plateau':
            return self.plateau_mswd
        else:
            return self.mswd

    def get_preferred_mswd_tuple(self):
        pv = self._get_pv('age')
        k = pv.computed_kind.lower()
        t = self.get_mswd_tuple()
        if k == 'plateau':
            t = self.get_plateau_mswd_tuple()

        return t

    def set_preferred_kinds(self, sg=None):
        naliquots = len({a.aliquot for a in self.analyses})
        default_ek = MSEM if naliquots > 1 else SD
        default_vk = WEIGHTED_MEAN if naliquots > 1 else DEFAULT_INTEGRATED

        for k in SUBGROUPING_ATTRS:
            if sg is None:
                if k == 'age':
                    # if only 1 aliquot in group assume step heat
                    if naliquots > 1:
                        vk, ek = WEIGHTED_MEAN, MSEM
                    else:
                        vk, ek = PLATEAU_ELSE_WEIGHTED_MEAN, MSEM
                else:
                    vk = default_vk
                    ek = default_ek
            else:
                vk = sg.get('{}_kind'.format(k), default_vk)
                ek = sg.get('{}_error_kind'.format(k), default_ek)

            self.set_preferred_kind(k, vk, ek)

    def set_preferred_kind(self, attr, k, ek):
        pv = self._get_pv(attr)
        pv.error_kind = ek
        pv.kind = k
        pv.dirty = True

    def get_preferred_kind(self, attr):
        pv = self.get_preferred_obj(attr)
        return pv.kind

    def get_preferred_obj(self, attr):
        if attr == 'age':
            # force preferred age
            _ = self.preferred_age

        pv = self._get_pv(attr)
        return pv

    # get preferred objects
    def _get_preferred_age(self):
        pa = ufloat(0, 0)

        pv = self._get_pv('age')
        pak = pv.kind.lower().replace(' ', '_')
        pv.computed_kind = pv.kind
        if pak in ('weighted_mean', 'wt._mean'):
            pa = self.weighted_age
        elif pak == 'arithmetic_mean':
            pa = self.arith_age
        elif pak == 'isochron':
            pa = self.isochron_age
        elif pak == 'integrated':
            pa = self._calculate_integrated('age', 'valid', pv.weighting)
        elif pak == 'plateau':
            pa = self.plateau_age
        elif pak == 'valid_integrated':
            pa = self._calculate_integrated('age', 'valid', pv.weighting)
        elif pak == 'total_integrated':
            pa = self._calculate_integrated('age', 'total', pv.weighting)
        elif pak == 'plateau_integrated':
            pa = self._calculate_integrated('age', 'plateau', pv.weighting)
        elif pak == 'plateau_else_weighted_mean':
            pa = self.plateau_age
            pv.computed_kind = 'Plateau'
            if not self.plateau_steps:
                pa = self.weighted_age
                pv.computed_kind = WEIGHTED_MEAN

        return pa

    def _get_preferred_(self, attr, kind, error_kind, weighting):
        setattr(self, '{}_error_kind'.format(attr), error_kind)
        self.dirty = True

        pk = kind.lower().replace(' ', '_')
        if pk == 'weighted_mean':
            pa = self._get_weighted_mean(attr)
        elif pk == 'valid_integrated':
            pa = self._calculate_integrated(attr, 'valid', weighting)
        elif pk == 'total_integrated':
            pa = self._calculate_integrated(attr, 'total', weighting)
        elif pk == 'plateau_integrated':
            pa = self._calculate_integrated(attr, 'plateau', weighting)
        elif pk == 'plateau_else_valid_integrated':
            if self.plateau_age:
                kind = 'Plateau'
                pa = self._calculate_integrated(attr, 'plateau', weighting)
            else:
                kind = 'Valid'
                pa = self._calculate_integrated(attr, 'valid', weighting)
        else:
            pa = self._calculate_arithmetic_mean(attr)

        if isinstance(pa, tuple):
            pa = ufloat(*pa)
        return pa, kind

    def _name_default(self):
        name = ''
        if self.analyses:
            name = make_aliquot(self.aliquot)
        return name

    def _get_nanalyses(self):
        pv = self._get_pv('age')
        k = pv.computed_kind.lower()

        if k == 'plateau':
            n = self.nsteps
        else:
            n = super(InterpretedAgeGroup, self)._get_nanalyses()
        return n

    def _value_string(self, t):
        try:
            v = getattr(self, t)
            a, e = nominal_value(v), std_dev(v)
        except AttributeError:
            a, e = NULL_STR, NULL_STR

        return a, e

    def __getattr__(self, item):
        return ''

# ============= EOF =============================================
