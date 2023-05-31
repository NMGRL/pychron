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

# ============= standard library imports ========================
from __future__ import absolute_import
from __future__ import print_function

from copy import copy
from operator import itemgetter, attrgetter

from numpy import polyval
from uncertainties import ufloat, std_dev, nominal_value

from pychron.core.codetools.simple_timeit import timethis
from pychron.core.helpers.isotope_utils import sort_detectors
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.stats import calculate_weighted_mean
from pychron.processing.arar_constants import ArArConstants
from pychron.processing.argon_calculations import (
    calculate_f,
    abundance_sensitivity_correction,
    age_equation,
    calculate_flux,
    calculate_arar_decay_factors,
)
from pychron.processing.isotope import Blank
from pychron.processing.isotope_group import IsotopeGroup
from pychron.pychron_constants import ARGON_KEYS, ARAR_MAPPING


def value_error(uv):
    return {"value": float(nominal_value(uv)), "error": float(std_dev(uv))}


class ArArAge(IsotopeGroup):
    """
    High level representation of the ArAr attributes of an analysis.
    """

    position_jerr = 0
    j = None
    modeled_j = None
    model_j_kind = ""

    irradiation = None
    irradiation_level = None
    irradiation_position = None
    irradiation_time = 0
    production_name = None
    monitor_age = None
    monitor_reference = None

    chron_segments = None

    fixed_k3739 = None

    timestamp = None

    kca = 0
    cak = 0
    kcl = 0
    clk = 0
    radiogenic_yield = 0
    rad40 = 0
    total40 = 0
    k39 = None

    uF = None
    F = None
    F_err = None
    F_err_wo_irrad = None

    uage = None
    uage_w_j_err = None
    uage_w_position_err = None

    age = 0
    age_err = 0
    age_err_wo_j = 0
    age_err_wo_irrad = 0
    age_err_wo_j_irrad = 0

    ar39decayfactor = 0
    ar37decayfactor = 0

    Ar39_decay_corrected = None
    Ar37_decay_corrected = None

    sensitivity = 1e-17  # fA/torr
    sensitivity_units = "mol/fA"

    _missing_isotope_warned = False
    _kca_warning = False
    _kcl_warning = False
    _lambda_k = None

    discrimination = None
    weight = 0  # in milligrams
    rundate = None

    arar_mapping = ARAR_MAPPING
    exclude_from_isochron = False

    def __init__(self, *args, **kw):
        super(ArArAge, self).__init__(*args, **kw)
        self.arar_constants = ArArConstants()
        self.isotopes = {}
        self.non_ar_isotopes = {}
        self.computed = {}
        self.corrected_intensities = {}
        self.interference_corrections = {}
        self.production_ratios = {}
        self.temporary_ic_factors = {}
        self.discrimination = ufloat(1, 0)

    @property
    def f(self):
        return self.F

    @property
    def f_err(self):
        return self.F_err

    @property
    def k2o(self):
        """
            MolKTot=Mol39*F39K*9.54/(JVal*KAbund40*.01)
            // moles of K40; = 39ArK*( (lambda*J/(lambda epsilon + lambda epsion prime)); McDougall  H. p. 19 eq. 2.17
            a=MolKTot*94.2*100/(2*Weight)

        weight should be in milligrams
        @return:
        """
        k2o = 0
        if self.weight:
            k40_k = 0.0001167
            mw_k2o = 94.2
            klambda = 9.54
            moles_39k = self.computed["k39"] * self.sensitivity
            try:
                moles_k = moles_39k * klambda / (k40_k * nominal_value(self.j))
                k2o = (moles_k * mw_k2o * 100) / (2 * self.weight * 0.001)
            except ZeroDivisionError:
                pass

        return k2o

    @property
    def display_k2o(self):
        return "" if not self.weight else self.k2o

    @property
    def isochron3940(self):
        a = self.get_interference_corrected_value("Ar39")
        b = self.get_interference_corrected_value("Ar40")
        return a / b

    @property
    def isochron3640(self):
        a = self.get_interference_corrected_value("Ar36")
        b = self.get_interference_corrected_value("Ar40")
        return a / b

    @property
    def lambda_k(self):
        lk = self._lambda_k
        if lk is None:
            lk = self.arar_constants.lambda_k
        return lk

    @lambda_k.setter
    def lambda_k(self, v):
        self._lambda_k = v

    @property
    def display_k3739_mode(self):
        return (
            "Fixed"
            if self.fixed_k3739 or self.arar_constants.k3739_mode.lower() == "fixed"
            else "Normal"
        )

    def baseline_corrected_intercepts_to_dict(self):
        return {
            k: value_error(v.get_baseline_corrected_value())
            for k, v in self.iteritems()
        }

    def blanks_to_dict(self):
        return {
            k: value_error(v.blank.get_baseline_corrected_value())
            for k, v in self.iteritems()
        }

    def icfactors_to_dict(self):
        return {k: value_error(v.ic_factor) for k, v in self.iteritems()}

    def interference_corrected_values_to_dict(self):
        return {
            k: value_error(v.get_interference_corrected_value())
            for k, v in self.iteritems()
        }

    def ic_corrected_values_to_dict(self):
        return {k: value_error(v.get_ic_corrected_value()) for k, v in self.iteritems()}

    def decay_corrected_values_to_dict(self):
        return {
            k: value_error(v.get_decay_corrected_value()) for k, v in self.iteritems()
        }

    def get_error_component(self, key, uage=None):
        if uage is None:
            uage = self.uage_w_j_err

        ae = 0
        if uage:
            v = next(
                (
                    error
                    for (var, error) in uage.error_components().items()
                    if var.tag == key
                ),
                0,
            )

            ae = uage.std_dev
        if ae:
            return ((v / ae) ** 2) * 100
        else:
            return 0

    def get_non_ar_isotope(self, key):
        return self.non_ar_isotopes.get(key, ufloat(0, 0))

    def get_computed_value(self, key):
        return self.computed.get(key, ufloat(0, 0))

    def get_interference_corrected_value(self, iso):
        if iso in self.isotopes:
            return self.isotopes[iso].get_interference_corrected_value()
        else:
            return ufloat(0, 0, tag=iso)

    def get_corrected_ratio(self, n, d):
        isos = self.isotopes
        if n in isos and d in isos:
            try:
                nn = isos[n].get_interference_corrected_value()
                dd = isos[d].get_interference_corrected_value()
                return nn / dd
            except ZeroDivisionError:
                pass

    def map_isotope_key(self, k):
        return self.arar_mapping.get(k, k)

    def get_value(self, attr):
        attr = self.map_isotope_key(attr)

        r = ufloat(0, 0, tag=attr)
        if attr.endswith("bs"):
            iso = attr[:-2]
            if iso in self.isotopes:
                r = self.isotopes[iso].baseline.uvalue
        elif attr in ("uage", "uage_w_j_err", "uage_w_position_err", "uF"):
            r = getattr(self, attr)
        elif attr.startswith("u") and ("/" in attr or "_" in attr):
            attr = attr[1:]
            r = self.get_ratio(attr, non_ic_corr=True)
        elif attr == "icf_40_36":
            a40 = self.map_isotope_key("Ar40")
            a36 = self.map_isotope_key("Ar36")
            r = self.get_corrected_ratio(a40, a36)
        elif attr.endswith("ic"):
            # ex. attr='Ar40ic'
            isok = attr[:-2]
            try:
                r = self.isotopes[isok].ic_factor
            except KeyError:
                r = ufloat(0, 0)
        elif attr.endswith("DetIC"):
            r = ufloat(0, 0)
            ratio = attr.split(" ")[0]
            numkey, denkey = ratio.split("/")

            for name, isos in groupby_key(
                self.isotopes.values(), key=attrgetter("name")
            ):
                num, den = None, None
                for iso in isos:
                    if iso.detector == numkey:
                        num = iso.get_non_detector_corrected_value()
                    elif iso.detector == denkey:
                        den = iso.get_non_detector_corrected_value()

                    if num and den:
                        return num / den

        elif attr in self.computed:
            r = self.computed[attr]
        elif attr in self.isotopes:
            r = self.isotopes[attr].get_intensity()
        elif attr == "equilibration_age":
            r = self.equilibration_age()
        else:
            if hasattr(self, attr):
                r = getattr(self, attr)

        return r

    def set_cosmogenic_correction(self, rs, rc):
        self.arar_constants.set_cosmogenic_ratios(rs, rc)
        self.recalculate_age(force=True)

    def set_sensitivity(self, sens):
        for si in sorted(sens, key=itemgetter("create_date"), reverse=True):
            if si["create_date"] < self.rundate:
                self.sensitivity = si["sensitivity"]
                self.sensitivity_units = si["units"]
                break

    def set_temporary_uic_factor(self, k, refdet, uv):
        self.temporary_ic_factors[k] = uv

    def set_beta(self, n, beta, is_peak_hop):
        """
        this is a source discrimination correction and assumes detectors are already "perfectly" calibrated
        Requested by WiscAr for NGX.  They do detector calibration in IsoLinx (Iconia) and assume the detectors stay in
        calibration.  Measure Air to generate a source mass discrimination correction.

        :param beta:
        :param is_peak_hop:
        :return:
        """
        self.info("calculated beta value={} ispeakhop={}".format(beta, is_peak_hop))

        m40 = 39.9624

        if is_peak_hop:
            items = (("L2", 36.9668), ("L1", 37.9627), ("AX", 38.964))
        else:
            items = (
                ("Ar36", 35.9675),
                ("Ar37", 36.9668),
                ("Ar38", 37.9627),
                ("Ar39", 38.964),
            )

        for k, m in items:
            b = (m40 / m) ** beta
            v = 1 / b
            if is_peak_hop:
                iso = self.get_isotope(detector=k)
            else:
                iso = self.get_isotope(k)
            det = iso.detector
            self.temporary_ic_factors[det] = {"reference_detector": n, "value": v}
            self.info("setting ic factor={} to {}".format(det, v))

    def calculate_transform_ic_factor(self, det, variable, coefficients, tag=None):
        if variable == "TotalIntensity":
            x = 0
            for iso in self.isotopes:
                x += iso.get_intensity()
        elif variable == "ICFactor":
            iso = self.get_isotope(detector=det)
            x = iso.ic_factor
        else:
            x = self.get_value(variable)

        uv = polyval(coefficients, x)
        if tag:
            uv = ufloat(uv.nominal_value, uv.std_dev, tag=tag)

        self.temporary_ic_factors[det] = {
            "value": uv,
            "variable": variable,
            "scaling_value": nominal_value(x),
            "reference_detector": det,
            "coefficients": coefficients,
        }
        return uv

    def set_temporary_ic_factor(self, n, k, v, e, tag=None):
        uv = ufloat(v, e, tag=tag)
        self.temporary_ic_factors[k] = {
            "reference_detector": n,
            "value": uv,
        }
        return uv

    def set_temporary_blank(self, k, v, e, f, verbose=False):
        if verbose:
            self.debug("temp blank {}({:0.4f}+/-{:0.4f}) fit={}".format(k, v, e, f))

        if k in self.isotopes:
            iso = self.isotopes[k]
            tb = iso.temporary_blank
            if tb is None:
                iso.temporary_blank = tb = Blank(iso.name, iso.detector)

            tb.value, tb.error, tb.fit = v, e, f

    def set_j(self, s, e):
        self.j = ufloat(s, std_dev=e, tag="J")

    def model_j(self, monitor_age, lambda_k):
        j = calculate_flux(self.uF, monitor_age, lambda_k=lambda_k)
        self.modeled_j = j
        return j

    def recalculate_age(self, force=False):
        if not self.uF or force:
            self._calculate_f()

        self._set_age_values(self.uF)

    def calculate_f(self):
        self.calculate_decay_factors()
        self._calculate_f()

    def calculate_no_interference(self):
        self._calculate_age(interferences={})

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
            dc37 = nominal_value(arc.lambda_Ar37)
            dc39 = nominal_value(arc.lambda_Ar39)
            a37df, a39df = calculate_arar_decay_factors(dc37, dc39, self.chron_segments)
            self.ar37decayfactor = a37df
            self.ar39decayfactor = a39df

    def instant_age(self, window=None, count=None):
        self.calculate_decay_factors()

        iso_intensities = self._assemble_isotope_intensities(window=window, count=count)
        if not iso_intensities:
            return

        f, f_wo_irrad, non_ar, computed, interference_corrected = self._calculate_f(
            iso_intensities=iso_intensities, set_attr=False
        )
        age = age_equation(
            nominal_value(self.j),
            f,
            # include_decay_error=include_decay_error,
            arar_constants=self.arar_constants,
        )
        return age

    def equilibration_ratios(self, num, den):
        num = self.isotopes[self.arar_mapping[num]]
        den = self.isotopes[self.arar_mapping[den]]
        counts = list(range(1, num.sniff.xs.shape[0]))
        self.calculate_decay_factors()

        numscalar = 1
        if num == "Ar37":
            numscalar = self.ar37decayfactor
        elif num == "Ar39":
            numscalar = self.ar39decayfactor

        denscalar = 1
        if num == "Ar37":
            denscalar = self.ar37decayfactor
        elif num == "Ar39":
            denscalar = self.ar39decayfactor

        return counts, [
            num.get_intensity(count=i)
            * numscalar
            / den.get_intensity(count=i)
            * denscalar
            for i in counts
        ]

    def equilibration_age(self, n=5):
        """
        this is the average of the last n equlibration ages
        """

        counts, ages = timethis(self.equilibration_ages)
        ages = ages[-n:]
        vs = [nominal_value(a) for a in ages]
        es = [std_dev(a) for a in ages]
        return ufloat(*calculate_weighted_mean(vs, es))

    _eq_ages = None, None

    def equilibration_ages(self, force=False):
        counts, ages = self._eq_ages
        if not ages or force:
            self.calculate_decay_factors()

            iso = self.isotopes[self.arar_mapping["Ar40"]]
            counts = list(range(1, iso.sniff.xs.shape[0]))

            ages = [self.instant_age(count=i) for i in counts]
            self._eq_ages = counts, ages

        return counts, ages

    # private
    def _calculate_kca(self):
        # self.debug('calculated kca')

        k = self.get_computed_value("k39")
        ca = self.get_non_ar_isotope("ca37")

        # print('{} k39={} ca37={}'.format(self, k, ca))
        prs = self.production_ratios
        k_ca_pr = 1
        if prs:
            cak = prs.get("Ca_K", 1)
            if not cak:
                cak = 1.0

            k_ca_pr = 1 / cak

        try:
            self.kca = k / ca * k_ca_pr
            self.cak = 1 / self.kca
        except ZeroDivisionError:
            self.kca = ufloat(0, 0)
            if not self._kca_warning:
                self._kca_warning = True
                self.debug("ca37 is zero. can't calculated k/ca")

    def _calculate_kcl(self):
        k = self.get_computed_value("k39")
        cl = self.get_non_ar_isotope("cl38")

        prs = self.production_ratios
        k_cl_pr = 1
        if prs:
            clk = prs.get("Cl_K", 1)
            if not clk:
                clk = 1.0

            k_cl_pr = 1 / clk
        try:
            self.kcl = k / cl * k_cl_pr
            self.clk = 1 / self.kcl
        except ZeroDivisionError:
            self.kcl = ufloat(0, 0)
            if not self._kcl_warning:
                self._kcl_warning = True
                self.warning("cl38 is zero. can't calculated k/cl")

    def _assemble_ar_ar_isotopes(self, **kw):
        isotopes = self.isotopes
        for ik in self.arar_mapping.values():
            if ik not in isotopes:
                if not self._missing_isotope_warned:
                    self.warning(
                        'No isotope= "{}". Required for age calculation'.format(ik)
                    )
                self._missing_isotope_warned = True
                return
        else:
            self._missing_isotope_warned = False

        return [isotopes[self.arar_mapping[k]].get_intensity(**kw) for k in ARGON_KEYS]

    def _assemble_isotope_intensities(self, **kw):
        iso_intensities = self._assemble_ar_ar_isotopes(**kw)
        if not iso_intensities:
            self.debug("failed assembling isotopes")
            return

        arc = self.arar_constants
        iso_intensities = abundance_sensitivity_correction(
            iso_intensities, arc.abundance_sensitivity
        )

        # assuming all m/z(39) and m/z(37) is radioactive argon
        # non gettered hydrocarbons will have a multiplicative systematic influence
        iso_intensities[1] *= self.ar39decayfactor
        iso_intensities[3] *= self.ar37decayfactor
        return iso_intensities

    def _calculate_f(self, iso_intensities=None, interferences=None, set_attr=True):
        if iso_intensities is None:
            iso_intensities = self._assemble_isotope_intensities()

        if iso_intensities:
            if interferences is None:
                interferences = self.interference_corrections

            f, f_wo_irrad, non_ar, computed, interference_corrected = calculate_f(
                iso_intensities,
                decay_time=self.decay_days,
                interferences=interferences,
                arar_constants=self.arar_constants,
                fixed_k3739=self.fixed_k3739,
            )
            if set_attr:
                self.uF = f
                self.F = nominal_value(f)
                self.F_err = std_dev(f)
                self.F_err_wo_irrad = std_dev(f_wo_irrad)
            return f, f_wo_irrad, non_ar, computed, interference_corrected

    def _calculate_age(self, include_decay_error=None, interferences=None):
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

        isotopes = self.isotopes
        isotopes[self.arar_mapping["Ar37"]].decay_corrected = self.Ar37_decay_corrected
        isotopes[self.arar_mapping["Ar39"]].decay_corrected = self.Ar39_decay_corrected

        self.corrected_intensities = {k: v for k, v in zip(ARGON_KEYS, iso_intensities)}

        f, f_wo_irrad, non_ar, computed, interference_corrected = self._calculate_f(
            iso_intensities, interferences=interferences
        )
        self.non_ar_isotopes = non_ar
        self.computed = computed
        self.radiogenic_yield = computed["radiogenic_yield"]
        self.rad40 = computed["rad40"]
        self.total40 = computed["a40"]
        self.k39 = computed["k39"]

        for k, v in interference_corrected.items():
            isotopes[k].interference_corrected_value = v

        self._set_age_values(f, include_decay_error)

    def _set_age_values(self, f, include_decay_error=False):
        arc = self.arar_constants

        if self.j is None:
            return

        j = copy(self.j)
        j.tag = "Position"
        j.std_dev = self.position_jerr or 0
        age = age_equation(
            j, f, include_decay_error=include_decay_error, arar_constants=arc
        )

        # new_monitor_age = None
        # new_lambda_k = None
        # age = convert_age(age, new_monitor_age, new_lambda_k)
        self.uage_w_position_err = age

        age = age_equation(
            self.j, f, include_decay_error=include_decay_error, arar_constants=arc
        )
        # age = convert_age(age, new_monitor_age, new_lambda_k)
        self.uage_w_j_err = age

        j = copy(self.j)
        j.std_dev = 0
        age = age_equation(
            j, f, include_decay_error=include_decay_error, arar_constants=arc
        )
        # age = convert_age(age, new_monitor_age, new_lambda_k)
        self.uage = age
        self.age = nominal_value(age)
        self.age_err = std_dev(age)
        self.age_err_wo_j = std_dev(age)

        for iso in self.itervalues():
            iso.age_error_component = self.get_error_component(iso.name)

    @property
    def detector_keys(self):
        return sort_detectors(set((d.detector for d in self.isotopes.values())))

    @property
    def irradiation_label(self):
        return "{}{} {}".format(
            self.irradiation, self.irradiation_level, self.irradiation_position
        )

    @property
    def decay_days(self):
        """
        return number of days since irradiation
        """
        return (self.timestamp - self.irradiation_time) / (60 * 60 * 24)

    @property
    def moles_k39(self):
        if self.k39 is None:
            self.calculate_age(force=True)
        return self.sensitivity * self.k39

    @property
    def signal_k39(self):
        if self.k39 is None:
            self.calculate_age(force=True)
        return self.k39

    @property
    def moles_Ar40(self):
        return self.sensitivity * self.get_isotope("Ar40").get_intensity()


# ============= EOF =============================================
