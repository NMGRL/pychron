#===============================================================================
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
#===============================================================================


#============= enthought library imports =======================
from traits.api import Dict, Property, Instance, Float, Str, List, Either
from pychron.pychron_constants import ARGON_KEYS
#============= standard library imports ========================
from uncertainties import ufloat, Variable, AffineScalarFunc

#============= local library imports  ==========================
from pychron.processing.argon_calculations import calculate_R, abundance_sensitivity_correction, age_equation, calculate_decay_factor
from pychron.processing.arar_constants import ArArConstants
from pychron.processing.isotope import Isotope

from pychron.loggable import Loggable
from pychron.helpers.isotope_utils import sort_isotopes


#def AgeProperty():
#    return Property(depends_on='age_dirty')
#

arar_constants = None


class ArArAge(Loggable):
    j = Either(Variable, AffineScalarFunc)
    irradiation = Str
    irradiation_level = Str
    irradiation_pos = Str
    irradiation_time = Float

    irradiation_label = Property(depends_on='irradiation, irradiation_level,irradiation_pos')

    #irradiation_info = Tuple
    chron_segments = List
    interference_corrections = Dict
    production_ratios = Dict

    timestamp = Float
    decay_days = Property(depends_on='timestamp,irradiation_time')
    #include_j_error = Bool(True)
    #include_irradiation_error = Bool(True)
    #include_decay_error = Bool(False)

    #arar_result = Dict
    #arar_updated=Event

    #rad40 = AgeProperty()
    #k39 = AgeProperty()
    #ca37 = AgeProperty()
    #cl36 = AgeProperty()
    #rad40_percent = AgeProperty()
    #
    kca = Either(Variable, AffineScalarFunc)#AgeProperty()
    cak = Either(Variable, AffineScalarFunc)#AgeProperty()
    kcl = Either(Variable, AffineScalarFunc)#AgeProperty()
    clk = Either(Variable, AffineScalarFunc)#AgeProperty()
    rad40_percent = Either(Variable, AffineScalarFunc)
    # ratios
    #Ar40_39 = AgeProperty()
    #Ar37_39 = AgeProperty()
    #Ar36_39 = AgeProperty()
    #
    #sensitivity = Property
    #sensitivity_multiplier = Property
    #_sensitivity_multiplier = Float

    isotopes = Dict
    isotope_keys = Property
    non_ar_isotopes = Dict

    R = Float
    R_err = Float
    R_err_wo_irrad = Float

    uage = Either(Variable, AffineScalarFunc)

    age = Float
    age_err = Float
    age_err_wo_j = Float
    age_err_wo_irrad = Float
    age_err_wo_j_irrad = Float

    #age_error = AgeProperty()
    #age_error_wo_j = AgeProperty()
    #age_dirty = Event
    #
    #Ar40 = AgeProperty()
    #Ar39 = AgeProperty()
    #Ar38 = AgeProperty()
    #Ar37 = AgeProperty()
    #Ar36 = AgeProperty()
    #Ar40_error = AgeProperty()
    #Ar39_error = AgeProperty()
    #Ar38_error = AgeProperty()
    #Ar37_error = AgeProperty()
    #Ar36_error = AgeProperty()
    #
    #moles_Ar40 = AgeProperty()
    #moles_K39 = AgeProperty()

    ar39decayfactor = Float
    ar37decayfactor = Float

    arar_constants = Instance(ArArConstants)

    moles_Ar40 = Float
    #def __init__(self, *args, **kw):
    #    super(ArArAge, self).__init__(*args, **kw)
    #self.age = ufloat(0, 0)

    def get_ic_factor(self, det):
        factors = self.arar_constants.ic_factors
        ic = 1, 1e-20
        if factors:
            ic = next(((ic.value, ic.error) for ic in factors
                       if ic.detector.lower() == det.lower()), (1.0, 1e-20))
        r = ufloat(*ic)
        return r

    def get_error_component(self, key):
        v = next((error for (var, error) in self.uage.error_components().items()
                  if var.tag == key), 0)

        ae = self.uage.std_dev
        if ae:
            return v ** 2 / ae ** 2 * 100
        else:
            return 0

    #def get_signal_value(self, k):
    #    return self._get_arar_result_attr(k)

    def clear_baselines(self):
        for k in self.isotopes:
            self.set_baseline(k, (0, 0))

    def clear_blanks(self):
        for k in self.isotopes:
            self.set_blank(k, (0, 0))

    def clear_error_components(self):
        for iso in self.isotopes.itervalues():
            iso.age_error_component = 0

    def set_isotope_detector(self, det):
        name, det = det.isotope, det.name
        if name in self.isotopes:
            iso = self.isotopes[name]
        else:
            iso = Isotope(name=name)
            self.isotopes[name] = iso

        iso.detector = det
        iso.ic_factor = self.get_ic_factor(det).nominal_value

    def get_isotope(self, name=None, detector=None):
        if name is None and detector is None:
            raise NotImplementedError('name or detector required')

        if name:
            return self.isotopes[name]
            #attr = 'name'
        else:
            attr = 'detector'
            value = detector
            return next((iso for iso in self.isotopes.itervalues()
                         if getattr(iso, attr) == value), None)

    def set_isotope(self, iso, v, **kw):
        if not self.isotopes.has_key(iso):
            niso = Isotope(name=iso)
            self.isotopes[iso] = niso
        else:
            niso = self.isotopes[iso]

        niso.set_uvalue(v)
        niso.trait_set(**kw)

        return niso

    def set_blank(self, iso, v):
        if not self.isotopes.has_key(iso):
            niso = Isotope(name=iso)
            self.isotopes[iso] = niso

        self.isotopes[iso].blank.set_uvalue(v)

    def set_baseline(self, iso, v):
        if not self.isotopes.has_key(iso):
            niso = Isotope(name=iso)
            self.isotopes[iso] = niso

        self.isotopes[iso].baseline.set_uvalue(v)

    def calculate_age(self, force=False, **kw):
        """
            force: force recalculation of age. necessary if you want error components
        """

        if not self.age or force:
            self._calculate_age(**kw)

            self._calculate_kca()
            self._calculate_kcl()

    #    #print 'calc', self.age, force
    #    #        self.debug('calculate age ={}'.format(self.age))
    #    if not self.age or force:
    ##        #self.age=timethis(self._calculate_age, kwargs=kw, msg='calculate_age')
    #        self.age = self._calculate_age(**kw)
    ##
    ##        self.age_dirty = True
    #    return self.age

    def get_non_ar_isotope(self, key):
        return self.non_ar_isotopes.get(key, ufloat(0, 0))

    def get_computed_value(self, key):
        return self.computed.get(key, ufloat(0, 0))

    def _calculate_kca(self):
        #self.debug('calculated kca')

        k = self.get_computed_value('k39')
        ca = self.get_non_ar_isotope('ca37')
        prs = self.production_ratios

        k_ca_pr = 1
        if prs:
            cak = prs.get('Ca_K', 1)
            if cak is None:
                cak = 1.0

            k_ca_pr = 1 / cak
        try:
            self.kca = k / ca * k_ca_pr
        except ZeroDivisionError:
            pass

    def _calculate_kcl(self):
        k = self.get_computed_value('k39')
        cl = self.get_non_ar_isotope('cl36')

        prs = self.production_ratios
        k_cl_pr = 1
        if prs:
            clk = prs.get('Cl_K', 1)
            if clk is None:
                clk = 1.0

            k_cl_pr = 1 / clk

        self.kcl = k / cl * k_cl_pr

    def _calculate_age(self, include_decay_error=None):
        #self.debug('calculate age')

        isos = []
        for ik in ARGON_KEYS:
            iso = self.isotopes[ik]
            iv = iso.get_intensity()
            isos.append(iv)

        arc = self.arar_constants
        isos = abundance_sensitivity_correction(isos, arc.abundance_sensitivity)

        a37df = calculate_decay_factor(arc.lambda_Ar37.nominal_value,
                                       self.chron_segments)

        a39df = calculate_decay_factor(arc.lambda_Ar39.nominal_value,
                                       self.chron_segments)
        self.ar37decayfactor = a37df
        self.ar39decayfactor = a39df

        isos[1] *= a39df
        isos[3] *= a37df

        R, R_wo_irrad, non_ar, computed, interference_corrected = calculate_R(isos,
                                                                              decay_time=self.decay_days,
                                                                              interferences=self.interference_corrections,
                                                                              arar_constants=self.arar_constants)

        self.non_ar_isotopes = non_ar
        self.computed = computed
        self.rad40_percent = computed['rad40_percent']
        for k, v in interference_corrected.iteritems():
            self.isotopes[k].interference_corrected_value = v

        self.R = R.nominal_value
        self.R_err = R.std_dev
        self.R_err_wo_irrad = R_wo_irrad.std_dev

        j = self.j.__copy__()
        age = age_equation(j, R, include_decay_error=include_decay_error,
                           arar_constants=self.arar_constants)

        self.uage = age

        self.age = float(age.nominal_value)
        self.age_err = float(age.std_dev)
        j.std_dev = 0
        self.age_err_wo_j = float(age.std_dev)

        j = self.j.__copy__()
        age = age_equation(j, R_wo_irrad, include_decay_error=include_decay_error,
                           arar_constants=self.arar_constants)

        self.age_err_wo_irrad = float(age.std_dev)
        j.std_dev = 0
        self.age_err_wo_j_irrad = float(age.std_dev)

        for iso in self.isotopes.itervalues():
            iso.age_error_component = self.get_error_component(iso.name)

    def _get_isotope_keys(self):
        keys = self.isotopes.keys()
        return sort_isotopes(keys)

    def _get_irradiation_label(self):
        return '{}{} {}'.format(self.irradiation,
                                self.irradiation_level,
                                self.irradiation_pos)

    def _get_decay_days(self):
        """
            return number of days since irradiation
        """
        return (self.timestamp - self.irradiation_time) / (60 * 60 * 24)

    #===============================================================================
    #
    #===============================================================================

    #def __getattr__(self, attr):
    #    if '/' in attr:
    #        #treat as ratio
    #        n, d = attr.split('/')
    #        try:
    #            return getattr(self, n) / getattr(self, d)
    #        except ZeroDivisionError:
    #            return ufloat(0, 1e-20)

    def _arar_constants_default(self):
        """
            use a global shared arar_constants
        """

        global arar_constants
        #self.debug('$$$$$$$$$$$$$$$$ {}'.format(arar_constants))
        #print 'asdf', arar_constants
        if arar_constants is None:
            arar_constants = ArArConstants()
            #return ArArConstants()
        return arar_constants

        #============= EOF =============================================
        #def load_irradiation(self, ln):
        #    self.timestamp = self._load_timestamp(ln)
        #
        #    self.interference_corrections=self._load_interference_corrections()
        #    self.chron_segments=self._load_chron_segments()
        #    self.decay_time=self._load_decay_time()
        #
        #    #self.irradiation_info = self._get_irradiation_info(ln)
        #    self.j = self._get_j(ln)
        #
        #    self.production_ratios = self._get_production_ratios(ln)

        #def _make_ic_factors_dict(self):
        #    ic_factors = dict()
        #    for ki in ARGON_KEYS:
        #        if ki in self.isotopes:
        #            iso = self.isotopes[ki]
        #            ic_factors[ki] = self.get_ic_factor(iso.detector)
        #
        #    return ic_factors
        #         @on_trait_change('age_dirty')
        #    def _handle_arar_result(self, new):
        #        #load error components into isotopes
        #        for iso in self.isotopes.itervalues():
        #            iso.age_error_component = self.get_error_component(iso.name)
        #            print iso.name, iso.age_error_component
        #================================================================================
        # private
        #================================================================================
        #
        #def _calculate_age2(self, include_j_error=None, include_decay_error=None, include_irradiation_error=None):
        #    if include_decay_error is None:
        #        include_decay_error = self.include_decay_error
        #    else:
        #        self.include_decay_error = include_decay_error
        #
        #    if include_j_error is None:
        #        include_j_error = self.include_j_error
        #    else:
        #        self.include_j_error = include_j_error
        #
        #    if include_irradiation_error is None:
        #        include_irradiation_error = self.include_irradiation_error
        #    else:
        #        self.include_irradiation_error = include_irradiation_error
        #
        #    fsignals = self._make_signals()
        #    bssignals = self._make_signals(kind='baseline')
        #    blsignals = self._make_signals(kind='blank')
        #    bksignals = self._make_signals(kind='background')
        #
        #    ic_factors = self._make_ic_factors_dict()
        #
        #    irrad = self.irradiation_info
        #    result = None
        #    if irrad:
        #        if not include_irradiation_error:
        #            #set errors to zero
        #            nirrad = []
        #            for ir in irrad[:-2]:
        #                nirrad.append((ir[0], 0))
        #            nirrad.extend(irrad[-2:])
        #            irrad = nirrad
        #
        #        ab = self.arar_constants.abundance_sensitivity
        #        result = calculate_arar_age(fsignals, bssignals, blsignals, bksignals,
        #                                    self.j, irrad, abundance_sensitivity=ab,
        #                                    ic_factors=ic_factors,
        #                                    discrimination=self.discrimination,
        #                                    #ic=ic,
        #                                    #ic=self.ic_factor,
        #                                    include_decay_error=include_decay_error,
        #                                    arar_constants=self.arar_constants)
        #
        #    if result:
        #        self.arar_result = result
        #        ai = result['age']
        #    else:
        #        ai = ufloat(0, 1.e-20)
        #
        #    ai = ai / self.arar_constants.age_scalar
        #
        #    return ai


        #def _make_signals(self, kind=None):
        #    isos = self.isotopes
        #    #        print isos
        #    def func(k):
        #        tag = k if kind is None else '{}_{}'.format(k, kind)
        #        #             if kind is None:
        #        #                 tag = k
        #        #             else:
        #        #                 tag = '{}_{}'.format(k, kind)
        #        if k in isos:
        #            iso = isos[k]
        #            if kind:
        #                iso = getattr(iso, kind)
        #            return iso.value, iso.error, tag
        #        else:
        #            return 0, 1e-20, tag
        #
        #    return (func(ki)
        #            for ki in ARGON_KEYS)

        #===============================================================================
        # property get/set
        #===============================================================================
        #def _get_production_ratios(self):
        #    return dict(Ca_K=1, Cl_K=1)

        #@cached_property
        #def _get_kca(self):
        #    return self._calculate_kca()
        #
        #@cached_property
        #def _get_cak(self):
        #    try:
        #        return 1 / self.kca
        #    except ZeroDivisionError:
        #        return 0
        #
        #@cached_property
        #def _get_kcl(self):
        #    return self._calculate_kcl()
        #
        #@cached_property
        #def _get_clk(self):
        #    try:
        #        return 1 / self.kcl
        #    except ZeroDivisionError:
        #        return ufloat(0, 0)

        #    @cached_property
        #    def _get_signals(self):
        # #        if not self._signals:
        # #        self._load_signals()
        #
        #        return self._signals

        #     @cached_property
        #     def _get_age(self):
        #         print 'ggggg'
        #         r = self._calculate_age()
        #         return r

        #     @cached_property

        #def _get_age_error(self):
        #    return self.age.std_dev
        #
        ##     @cached_property
        #def _get_age_error_wo_j(self):
        #    try:
        #        return float(self.arar_result['age_err_wo_j'] / self.arar_constants.age_scalar)
        #    except KeyError:
        #        return 1e-20

        #     @cached_property
        #     def _get_timestamp(self):
        #         return datetime.now()

        #def _get_irradiation_info(self, ln):
        ##         '''
        ##             return k4039, k3839,k3739, ca3937, ca3837, ca3637, cl3638, chronsegments, decay_time
        ##         '''
        #    prs = (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), [], 1
        #    return prs
        #
        #def _get_j(self):
        #    s = 1.e-4
        #    e = 1e-6
        #
        #    return ufloat(s, e, 'j')

        #def _get_rad40(self):
        #    return self._get_arar_result_attr('rad40')
        #
        #def _get_k39(self):
        #    return self._get_arar_result_attr('k39')
        #
        #def _get_ca37(self):
        #    return self._get_arar_result_attr('ca37')
        #
        #def _get_cl36(self):
        #    return self._get_arar_result_attr('ca37')
        #
        #def _get_R(self):
        #    try:
        #        return self.rad40 / self.k39
        #    except (ZeroDivisionError, TypeError):
        #        return ufloat(0, 1e-20)

        #def _get_rad40_percent(self):
        #    try:
        #        return self.rad40 / self.Ar40 * 100
        #    except (ZeroDivisionError, TypeError), e:
        #        self.debug('Rad40 Percent error {}'.format(e))
        #        return ufloat(0, 1e-20)

        #def _get_Ar40(self):
        #
        #    return self._get_arar_result_attr('Ar40')
        #
        #def _get_Ar39(self):
        #    return self._get_arar_result_attr('Ar39')
        #
        #def _get_Ar38(self):
        #    return self._get_arar_result_attr('Ar38')
        #
        #def _get_Ar37(self):
        #    return self._get_arar_result_attr('Ar37')
        #
        #def _get_Ar36(self):
        #    return self._get_arar_result_attr('Ar36')
        #
        #def _get_Ar40_error(self):
        #    r = self._get_arar_result_attr('Ar40')
        #    if r:
        #        return r.std_dev
        #
        #def _get_Ar39_error(self):
        #    r = self._get_arar_result_attr('Ar39')
        #    if r:
        #        return r.std_dev
        #
        #def _get_Ar38_error(self):
        #    r = self._get_arar_result_attr('Ar38')
        #    if r:
        #        return r.std_dev
        #
        #def _get_Ar37_error(self):
        #    r = self._get_arar_result_attr('Ar37')
        #    if r:
        #        return r.std_dev

        #def _get_Ar36_error(self):
        #    r = self._get_arar_result_attr('Ar36')
        #    if r:
        #        return r.std_dev
        #
        #def _get_moles_Ar40(self):
        #    return 0.001
        #
        #def _get_moles_K39(self):
        #    return self.k39 * self.sensitivity * self.sensitivity_multiplier
        #
        #def _get_ic_factor(self):
        #    return ufloat(self.arar_constants.ic_factor_v,
        #                  self.arar_constants.ic_factor_e, 'ic_factor')
        #
        ##     @cached_property
        #def _get_Ar40_39(self):
        #    try:
        #        return self.rad40 / self.k39
        #    except ZeroDivisionError:
        #        return ufloat(0, 0)
        #
        #        #     @cached_property
        #
        #def _get_Ar37_39(self):
        #    try:
        #        return self.Ar37 / self.Ar39
        #    except ZeroDivisionError:
        #        return ufloat(0, 0)
        #
        #        #     @cached_property
        #
        #def _get_Ar36_39(self):
        #    try:
        #        return self.Ar36 / self.Ar39
        #    except ZeroDivisionError:
        #        return ufloat(0, 0)
        #
        #def _get_sensitivity(self):
        #    return 1.0
        #
        #def _set_sensitivity_multiplier(self, v):
        #    self._sensitivity_multiplier = v
        #
        #def _get_sensitivity_multiplier(self):
        #    return self._sensitivity_multiplier

        #def _get_arar_result_attr(self, key):
        ##        print self.arar_result.keys()
        #    if key in self.arar_result:
        #        return self.arar_result[key]
        #    elif key in self.isotopes:
        #        return self.isotopes[key].uvalue
        #    else:
        #        keys = self.arar_result.keys()
        #        #self.warning('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ NO KEY {} {}'.format(key, keys))
        #        return ufloat(0, 1e-20)