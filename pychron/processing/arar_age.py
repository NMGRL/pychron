# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Dict, Property, Instance, Float, Str, List, Either, cached_property
# ============= standard library imports ========================
from uncertainties import ufloat, Variable, AffineScalarFunc
from copy import copy
# ============= local library imports  ==========================
from pychron.processing.isotope_group import IsotopeGroup
from pychron.processing.argon_calculations import calculate_F, abundance_sensitivity_correction, age_equation, \
    calculate_decay_factor
from pychron.processing.arar_constants import ArArConstants
from pychron.pychron_constants import ARGON_KEYS


class ArArAge(IsotopeGroup):
    """
    High level representation of the ArAr attributes of an analysis.
    """
    j = Either(Variable, AffineScalarFunc)
    irradiation = Str
    irradiation_level = Str
    irradiation_pos = Str
    irradiation_time = Float
    production_name = Str

    irradiation_label = Property(depends_on='irradiation, irradiation_level,irradiation_pos')

    chron_segments = List
    chron_dosages = List
    interference_corrections = Dict
    production_ratios = Dict

    fixed_k3739 = None

    timestamp = Float
    decay_days = Property(depends_on='timestamp,irradiation_time')

    kca = Either(Variable, AffineScalarFunc)
    cak = Either(Variable, AffineScalarFunc)
    kcl = Either(Variable, AffineScalarFunc)
    clk = Either(Variable, AffineScalarFunc)
    rad40_percent = Either(Variable, AffineScalarFunc)

    non_ar_isotopes = Dict
    computed = Dict
    corrected_intensities = Dict

    uF = Either(Variable, AffineScalarFunc)
    F = Float
    F_err = Float
    F_err_wo_irrad = Float

    uage = Either(Variable, AffineScalarFunc)
    uage_wo_j_err = Either(Variable, AffineScalarFunc)

    age = Float
    age_err = Float
    age_err_wo_j = Float
    age_err_wo_irrad = Float
    age_err_wo_j_irrad = Float

    ar39decayfactor = Float
    ar37decayfactor = Float

    arar_constants = Instance(ArArConstants, ())

    Ar39_decay_corrected = Either(Variable, AffineScalarFunc)
    Ar37_decay_corrected = Either(Variable, AffineScalarFunc)

    moles_Ar40 = Property
    sensitivity = Float  # moles/pA

    _missing_isotope_warned = False
    _kca_warning = False
    _kcl_warning = False


    # def __init__(self, *args, **kw):
    # HasTraits.__init__(self, *args, **kw)
    #     self.logger = logger

        # super(ArArAge, self).__init__(*args, **kw)

    def set_j(self, s, e):
        self.j = ufloat(s, std_dev=e)

    def get_corrected_ratio(self, n, d):
        isos = self.isotopes
        if n in isos and d in isos:
            try:
                nn = isos[n].get_interference_corrected_value()
                dd = isos[d].get_interference_corrected_value()
                return nn / dd
            except ZeroDivisionError:
                pass

    # def get_detector_active(self, attr):
    #     det = next((i for i in self.isotopes if i.detector == attr), None)
    #     if det:
    #         pass
    def get_value(self, attr):
        r = ufloat(0, 0, tag=attr)
        if attr.endswith('bs'):
            iso = attr[:-2]
            if iso in self.isotopes:
                r = self.isotopes[iso].baseline.uvalue
        elif '/' in attr:
            non_ic_cor = attr.startswith('u')
            if non_ic_cor:
                attr = attr[1:]
            r = self.get_ratio(attr, non_ic_cor)
        elif attr == 'icf_40_36':
            r = self.get_corrected_ratio('Ar40', 'Ar36')
        elif attr.endswith('ic'):
            # ex. attr='Ar40ic'
            isok = attr[:-2]
            try:
                r = self.isotopes[isok].ic_factor
            except KeyError:
                r = ufloat(0, 0)

        elif attr in self.computed:
            r = self.computed[attr]
        elif attr in self.isotopes:
            r = self.isotopes[attr].get_intensity()
        elif hasattr(self, attr):
            r = getattr(self, attr)
        else:
            iso = self._get_iso_by_detector(attr)
            # iso=next((i for i in self.isotopes if i.detector==attr), None)
            if iso:
                r = ufloat(iso.ys[-1], tag=attr)

        return r

    def get_interference_corrected_value(self, iso):
        if iso in self.isotopes:
            return self.isotopes[iso].get_interference_corrected_value()
        else:
            return ufloat(0, 0, tag=iso)

    def calculate_F(self):
        self.calculate_decay_factors()
        self._calculate_F()

    # @caller
    def calculate_age(self, force=False, **kw):
        """
            force: force recalculation of age. necessary if you want error components
        """

        if not self.age or force:
            self.calculate_decay_factors()

            self._calculate_age(**kw)
            self._calculate_kca()
            self._calculate_kcl()

    def calculate_decay_factors(self):
        arc = self.arar_constants
        # only calculate decayfactors once
        if not self.ar39decayfactor:
            a37df = calculate_decay_factor(arc.lambda_Ar37.nominal_value,
                                           self.chron_segments)
            a39df = calculate_decay_factor(arc.lambda_Ar39.nominal_value,
                                           self.chron_segments)
            self.ar37decayfactor = a37df
            self.ar39decayfactor = a39df

    def get_non_ar_isotope(self, key):
        return self.non_ar_isotopes.get(key, ufloat(0, 0))

    def get_computed_value(self, key):
        return self.computed.get(key, ufloat(0, 0))

    # def warning(self, *args, **kw):
    #     self.logger.warning(*args, **kw)
    #
    # def debug(self, *args, **kw):
    #     self.logger.debug(*args, **kw)

    def _calculate_kca(self):
        # self.debug('calculated kca')

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
            self.kca = ufloat(0, 0)
            if not self._kca_warning:
                self._kca_warning = True
                self.debug("ca37 is zero. can't calculated k/ca")

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
        try:
            self.kcl = k / cl * k_cl_pr
        except ZeroDivisionError:
            self.kcl = ufloat(0, 0)
            if not self._kcl_warning:
                self._kcl_warning = True
                self.warning("cl36 is zero. can't calculated k/cl")

    def _assemble_ar_ar_isotopes(self):
        isotopes = self.isotopes
        for ik in ARGON_KEYS:
            try:
                isotopes[ik]
            except KeyError:
                if not self._missing_isotope_warned:
                    self.warning('No isotope= "{}". Required for age calculation'.format(ik))
                self._missing_isotope_warned = True
                return
        else:
            self._missing_isotope_warned = False

        return [isotopes[ik].get_intensity() for ik in ARGON_KEYS]

    def _calculate_F(self, iso_intensities=None):
        if iso_intensities is None:
            iso_intensities = self._assemble_isotope_intensities()

        if iso_intensities:
            ifc = self.interference_corrections
            f, f_wo_irrad, non_ar, computed, interference_corrected = calculate_F(iso_intensities,
                                                                                  decay_time=self.decay_days,
                                                                                  interferences=ifc,
                                                                                  arar_constants=self.arar_constants,
                                                                                  fixed_k3739=self.fixed_k3739)
            self.uF = f
            self.F = f.nominal_value
            self.F_err = f.std_dev
            self.F_err_wo_irrad = f_wo_irrad.std_dev
            return f, f_wo_irrad, non_ar, computed, interference_corrected

    def _assemble_isotope_intensities(self):
        iso_intensities = self._assemble_ar_ar_isotopes()
        if not iso_intensities:
            self.debug('failed assembling isotopes')
            return

        arc = self.arar_constants
        iso_intensities = abundance_sensitivity_correction(iso_intensities, arc.abundance_sensitivity)

        #assuming all m/z(39) and m/z(37) is radioactive argon
        #non gettered hydrocarbons will have a multiplicative systematic influence
        iso_intensities[1] *= self.ar39decayfactor
        iso_intensities[3] *= self.ar37decayfactor
        return iso_intensities

    def _calculate_age(self, include_decay_error=None):
        """
            approx 2/3 of the calculation time is in _assemble_ar_ar_isotopes.
            Isotope.get_intensity takes about 5ms.
        """
        # self.debug('calculate age')
        iso_intensities = self._assemble_isotope_intensities()
        if not iso_intensities:
            return

        self.Ar39_decay_corrected = iso_intensities[1]
        self.Ar37_decay_corrected = iso_intensities[3]

        self.isotopes['Ar37'].decay_corrected = self.Ar37_decay_corrected
        self.isotopes['Ar39'].decay_corrected = self.Ar39_decay_corrected

        # self.debug('allow_negative ca correction {}'.format(arc.allow_negative_ca_correction))
        self.corrected_intensities = dict(Ar40=iso_intensities[0],
                                          Ar39=iso_intensities[1],
                                          Ar38=iso_intensities[2],
                                          Ar37=iso_intensities[3],
                                          Ar36=iso_intensities[4])

        f, f_wo_irrad, non_ar, computed, interference_corrected = self._calculate_F(iso_intensities)

        self.non_ar_isotopes = non_ar
        self.computed = computed
        self.rad40_percent = computed['rad40_percent']

        isotopes = self.isotopes
        for k, v in interference_corrected.iteritems():
            isotopes[k].interference_corrected_value = v

        if self.j is not None:
            j = copy(self.j)
        else:
            j = ufloat(1e-4, 1e-7)

        arc = self.arar_constants
        age = age_equation(j, f, include_decay_error=include_decay_error,
                           arar_constants=arc)
        self.uage = age
        self.age = age.nominal_value
        self.age_err = age.std_dev

        if self.j is not None:
            j = copy(self.j)
        else:
            j = ufloat(1e-4, 1e-7)

        j.std_dev = 0
        age = age_equation(j, f, include_decay_error=include_decay_error,
                           arar_constants=arc)

        self.age_err_wo_j = float(age.std_dev)
        self.uage_wo_j_err = ufloat(self.age, self.age_err_wo_j)

        if self.j is not None:
            j = copy(self.j)
        else:
            j = ufloat(1e-4, 1e-7)

        age = age_equation(j, f_wo_irrad, include_decay_error=include_decay_error,
                           arar_constants=arc)

        self.age_err_wo_irrad = age.std_dev
        j.std_dev = 0
        self.age_err_wo_j_irrad = age.std_dev

        for iso in isotopes.itervalues():
            iso.age_error_component = self.get_error_component(iso.name)

    def _get_irradiation_label(self):
        return '{}{} {}'.format(self.irradiation,
                                self.irradiation_level,
                                self.irradiation_pos)

    def _get_decay_days(self):
        """
            return number of days since irradiation
        """
        return (self.timestamp - self.irradiation_time) / (60 * 60 * 24)

    @cached_property
    def _get_moles_Ar40(self):
        return self.sensitivity * self.get_isotope('Ar40').get_intensity()


                # ===============================================================================
                #
                # ===============================================================================

                # def _arar_constants_default(self):
                #     """
                #         use a global shared arar_constants
                #     """
                #
                #     global arar_constants
                #     #self.debug('$$$$$$$$$$$$$$$$ {}'.format(arar_constants))
                #     #print 'asdf', arar_constants
                #     if arar_constants is None:
                #         arar_constants = ArArConstants()
                #         #return ArArConstants()
                #     return arar_constants

                # def _arar_constants_default(self):
                #     """
                #         use a global shared arar_constants
                #     """
                #
                #     global arar_constants
                #     #self.debug('$$$$$$$$$$$$$$$$ {}'.format(arar_constants))
                #     #print 'asdf', arar_constants
                #     if arar_constants is None:
                #         arar_constants = ArArConstants()
                #         #return ArArConstants()
                #     return arar_constants

                # ============= EOF =============================================
