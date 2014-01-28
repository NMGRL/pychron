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
from ConfigParser import ConfigParser
from copy import copy
import os
from traits.api import HasTraits, Dict, Property, Instance, Float, Str, List, Either
from pychron.core.helpers.logger_setup import new_logger
from pychron.paths import paths
from pychron.pychron_constants import ARGON_KEYS
#============= standard library imports ========================
from uncertainties import ufloat, Variable, AffineScalarFunc
from numpy import hstack
#============= local library imports  ==========================
from pychron.processing.argon_calculations import calculate_F, abundance_sensitivity_correction, age_equation, calculate_decay_factor
from pychron.processing.arar_constants import ArArConstants
from pychron.processing.isotope import Isotope, Baseline

from pychron.loggable import Loggable
from pychron.core.helpers.isotope_utils import sort_isotopes

logger=new_logger('ArArAge')
# arar_constants = None


class ArArAge(Loggable):
    j = Either(Variable, AffineScalarFunc)
    irradiation = Str
    irradiation_level = Str
    irradiation_pos = Str
    irradiation_time = Float

    irradiation_label = Property(depends_on='irradiation, irradiation_level,irradiation_pos')

    chron_segments = List
    interference_corrections = Dict
    production_ratios = Dict

    timestamp = Float
    decay_days = Property(depends_on='timestamp,irradiation_time')

    kca = Either(Variable, AffineScalarFunc)
    cak = Either(Variable, AffineScalarFunc)
    kcl = Either(Variable, AffineScalarFunc)
    clk = Either(Variable, AffineScalarFunc)
    rad40_percent = Either(Variable, AffineScalarFunc)

    isotopes = Dict
    isotope_keys = Property
    non_ar_isotopes = Dict
    computed = Dict

    uF = Either(Variable, AffineScalarFunc)
    F = Float
    F_err = Float
    F_err_wo_irrad = Float

    uage = Either(Variable, AffineScalarFunc)

    age = Float
    age_err = Float
    age_err_wo_j = Float
    age_err_wo_irrad = Float
    age_err_wo_j_irrad = Float

    ar39decayfactor = Float
    ar37decayfactor = Float

    arar_constants = Instance(ArArConstants,())
    logger=logger

    moles_Ar40 = Float

    _missing_isotope_warned = False
    _kca_warning = False
    _kcl_warning = False

    def __init__(self, *args, **kw):
        HasTraits.__init__(self, *args, **kw)
        self.logger=logger

    def clear_isotopes(self):
        for iso in self.isotopes:
            self.isotopes[iso] = Isotope(name=iso)

    def get_baseline(self, attr):
        if attr.endswith('bs'):
            attr=attr[:-2]

        if attr in self.isotopes:
            return self.isotopes[attr].baseline
        else:
            return Baseline()

    def has_attr(self, attr):
        if attr in self.computed:
            return True
        elif attr in self.isotopes:
            return True
        elif hasattr(self, attr):
            return True

    def get_value(self, attr):
        if attr in self.computed:
            return self.computed[attr]
        elif attr in self.isotopes:
            return self.isotopes[attr]
        elif hasattr(self, attr):
            return getattr(self, attr)
        else:
            return ufloat(0, 0, tag=attr)

    def get_interference_corrected_value(self, iso):
        if iso in self.isotopes:
            return self.isotopes[iso].get_interference_corrected_value()
        else:
            return ufloat(0,0, tag=iso)

    def get_ic_factor(self, det):
        # storing ic_factor in preferences causing issues
        # ic_factor stored in detectors.cfg

        p = os.path.join(paths.spectrometer_dir, 'detectors.cfg')
        # factors=None
        ic = 1, 1e-20
        if os.path.isfile(p):
            c=ConfigParser()
            c.read(p)
            det=det.lower()
            for si in c.sections():
                if si.lower()==det:
                    v,e=1,1e-20
                    if c.has_option(si, 'ic_factor'):
                        v=c.getfloat(si,'ic_factor')
                    if c.has_option(si, 'ic_factor_err'):
                        e=c.getfloat(si,'ic_factor_err')
                    ic=v,e
                    break
        else:
            self.debug('no detector file {}. cannot retrieve ic_factor'.format(p))

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
    def append_data(self, iso, det, x, signal, kind):
        for i in (iso, '{}{}'.format(iso,det)):
            if i in self.isotopes:
                ii = self.isotopes[i]
                if kind in ('sniff', 'baseline'):
                    ii = getattr(ii, kind)
                ii.xs = hstack((ii.xs, (x,)))
                ii.ys = hstack((ii.ys, (signal,)))
                return True

        # else:
        #     self.debug('failed appending data for {}. not a current isotope {}'.format(iso, self.isotope_keys))

    def clear_baselines(self):
        for k in self.isotopes:
            self.set_baseline(k, (0, 0))

    def clear_blanks(self):
        for k in self.isotopes:
            self.set_blank(k, (0, 0))

    def clear_error_components(self):
        for iso in self.isotopes.itervalues():
            iso.age_error_component = 0

    def isotope_factory(self, **kw):
        return Isotope(**kw)

    def set_isotope_detector(self, det, iso=None):
        if iso:
            name = iso

        if not isinstance(det, str):
            name, det = det.isotope, det.name

        if name in self.isotopes:
            iso = self.isotopes[name]
        else:
            iso = Isotope(name=name)
            self.isotopes[name] = iso

        iso.detector = det
        iso.ic_factor = self.get_ic_factor(det)

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

        self.debug('setting {} blank {}'.format(iso, v))
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
            self.calculate_decay_factors()

            self._calculate_age(**kw)
            self._calculate_kca()
            self._calculate_kcl()

    def calculate_decay_factors(self):
        arc = self.arar_constants
        #only calculate decayfactors once
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
            if not self._kcl_warning:
                self._kcl_warning = True
                self.warning("cl36 is zero. can't calculated k/cl")

    def _assemble_ar_ar_isotopes(self):
        isotopes = self.isotopes

        for ik in ARGON_KEYS:
            if not ik in isotopes:
                if not self._missing_isotope_warned:
                    self.warning('No isotope= "{}". Required for age calculation'.format(ik))
                self._missing_isotope_warned = True
                return
        else:
            self._missing_isotope_warned = False

        isos = [isotopes[ik].get_intensity() for ik in ARGON_KEYS]

        return isos

    def _calculate_age(self, include_decay_error=None):
        """
            approx 2/3 of the calculation time is in _assemble_ar_ar_isotopes.
            Isotope.get_intensity takes about 5ms.
        """
        isos = self._assemble_ar_ar_isotopes()
        if not isos:
            return

        arc = self.arar_constants
        isos = abundance_sensitivity_correction(isos, arc.abundance_sensitivity)
        isos[1] *= self.ar39decayfactor
        isos[3] *= self.ar37decayfactor

        # print isos[4]
        # print 'ifc',self.interference_corrections
        f, f_wo_irrad, non_ar, computed, interference_corrected = calculate_F(isos,
                                                                              decay_time=self.decay_days,
                                                                              interferences=self.interference_corrections,
                                                                              arar_constants=self.arar_constants)
        # print 'c',interference_corrected['Ar36']
        self.non_ar_isotopes = non_ar
        self.computed = computed
        self.rad40_percent = computed['rad40_percent']
        for k, v in interference_corrected.iteritems():
            self.isotopes[k].interference_corrected_value = v

        self.uF = f
        self.F = f.nominal_value
        self.F_err = f.std_dev
        self.F_err_wo_irrad = f_wo_irrad.std_dev

        if self.j is not None:
            j = copy(self.j)
        else:
            j = ufloat(1e-4,1e-7)

        age = age_equation(j, f, include_decay_error=include_decay_error,
                           arar_constants=self.arar_constants)

        self.uage = age

        self.age = float(age.nominal_value)
        self.age_err = float(age.std_dev)

        j.std_dev = 0
        self.age_err_wo_j = float(age.std_dev)

        if self.j is not None:
            j = copy(self.j)
        else:
            j = ufloat(1e-4, 1e-7)
        age = age_equation(j, f_wo_irrad, include_decay_error=include_decay_error,
                           arar_constants=self.arar_constants)

        self.age_err_wo_irrad = float(age.std_dev)
        j.std_dev = 0
        self.age_err_wo_j_irrad = float(age.std_dev)

        #print 'asddsadf'
        #print self.age_err
        #print self.age_err_wo_j
        #print self.age_err_wo_j_irrad

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

        #============= EOF =============================================
