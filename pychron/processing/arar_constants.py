#===============================================================================
# Copyright 2011 Jake Ross
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

#=============enthought library imports=======================
from apptools.preferences.preference_binding import PreferenceBinding
from traits.api import HasTraits, Property, Float, Enum, Str, List, Either
from uncertainties import ufloat

from pychron.core.ui.preference_binding import bind_preference
from pychron.pychron_constants import AGE_SCALARS

#=============local library imports  ==========================

class ICFactor(HasTraits):
    detector = Str
    value = Float


class ICFactorPreferenceBinding(PreferenceBinding):
    def _get_value(self, name, value):
        path = self.preference_path.split('.')[:-1]
        path.append('stored_ic_factors')
        path = '.'.join(path)
        ics = self.preferences.get(path)
        ics = eval(ics)
        ss = []
        for ic in ics:
            detector, v, e = ic.split(',')
            ss.append(ICFactor(detector=detector,
                               value=float(v),
                               error=float(e)
            ))
        return ss


class ArArConstants(HasTraits):
    lambda_b = Property(depends_on='lambda_b_v, lambda_b_e')
    lambda_b_v = Float(4.962e-10)
    lambda_b_e = Float(9.3e-13)
    lambda_e = Property(depends_on='lambda_e_v, lambda_e_e')
    lambda_e_v = Float(5.81e-11)
    lambda_e_e = Float(1.6e-13)

    lambda_k = Property
    lambda_Cl36 = Property(depends_on='lambda_Cl36_v, lambda_Cl36_e')
    lambda_Cl36_v = Float(6.3e-9)
    lambda_Cl36_e = Float(0)
    lambda_Ar37 = Property(depends_on='lambda_Ar37_v, lambda_Ar37_e')
    lambda_Ar37_v = Float(0.01975)
    lambda_Ar37_e = Float(0)
    lambda_Ar39 = Property(depends_on='lambda_Ar39_v, lambda_Ar39_e')
    lambda_Ar39_v = Float(7.068e-6)
    lambda_Ar39_e = Float(0)

    atm4036 = Property(depends_on='atm4036_v,atm4036_e')
    atm4036_v = Float(295.5)
    atm4036_e = Float(0.5)

    atm4038 = Property(depends_on='atm4038_v,atm4038_e')
    atm4038_v = Float(1575)
    atm4038_e = Float(2)

    atm3836 = Property(depends_on='atm4038_v,atm4038_e,atm4036_v,atm4036_e')

    abundance_40K = 0.000117
    mK = 39.0983
    mO = 15.9994

    k3739_mode = Enum('Normal', 'Fixed')
    fixed_k3739 = Property(depends_on='k3739_v, k3739_e')
    k3739_v = Float(0.01)
    k3739_e = Float(0.0001)

    age_units = Str('Ma')
    age_scalar = Property(depends_on='age_units')
    abundance_sensitivity = Float

    ic_factors = Either(List, Str)

    atm4036_citation = Str#'Nier (1950)'
    atm4038_citation = Str#'Nier (1950)'
    lambda_b_citation = Str#'Min (2008)'
    lambda_e_citation = Str#'Min (2008)'
    lambda_Ar39_citation = Str#'Min (2008)'
    lambda_Ar37_citation = Str#'Min (2008)'

    def __init__(self, *args, **kw):
        #print 'init arar constants'
        try:
            bind_preference(self, 'lambda_b_v', 'pychron.arar.constants.lambda_b')
            bind_preference(self, 'lambda_b_e', 'pychron.arar.constants.lambda_b_error')
            bind_preference(self, 'lambda_e_v', 'pychron.arar.constants.lambda_e')
            bind_preference(self, 'lambda_e_e', 'pychron.arar.constants.lambda_e_error')
            bind_preference(self, 'lambda_Cl36_v', 'pychron.arar.constants.lambda_Cl36')
            bind_preference(self, 'lambda_Cl36_e', 'pychron.arar.constants.lambda_Cl36_error')
            bind_preference(self, 'lambda_Ar37_v', 'pychron.arar.constants.lambda_Ar37')
            bind_preference(self, 'lambda_Ar37_e', 'pychron.arar.constants.lambda_Ar37_error')
            bind_preference(self, 'lambda_Ar39_v', 'pychron.arar.constants.lambda_Ar39')
            bind_preference(self, 'lambda_Ar39_e', 'pychron.arar.constants.lambda_Ar39_error')

            bind_preference(self, 'atm4036_v', 'pychron.arar.constants.Ar40_Ar36_atm')
            bind_preference(self, 'atm_4036_e', 'pychron.arar.constants.Ar40_Ar36_atm_error')
            bind_preference(self, 'atm4038_v', 'pychron.arar.constants.Ar40_Ar38_atm')
            bind_preference(self, 'atm_4038_e', 'pychron.arar.constants.Ar40_Ar38_atm_error')

            bind_preference(self, 'k3739_mode', 'pychron.arar.constants.Ar37_Ar39_mode')
            bind_preference(self, 'k3739_v', 'pychron.arar.constants.Ar37_Ar39')
            bind_preference(self, 'k3739_e', 'pychron.arar.constants.Ar37_Ar39_error')

            bind_preference(self, 'age_units', 'pychron.arar.constants.age_units')
            bind_preference(self, 'abundance_sensitivity', 'pychron.arar.constants.abundance_sensitivity')

            bind_preference(self, 'ic_factors', 'pychron.spectrometer.ic_factors',
                            factory=ICFactorPreferenceBinding)

            prefid = 'pychron.arar.constants'
            bind_preference(self, 'atm4036_citation', '{}.Ar40_Ar36_atm_citation'.format(prefid))
            bind_preference(self, 'atm4038_citation', '{}.Ar40_Ar38_atm_citation'.format(prefid))
            bind_preference(self, 'lambda_b_citation' '{}.lambda_b_citation'.format(prefid))
            bind_preference(self, 'lambda_e_citation', '{}.lambda_e_citation'.format(prefid))
            bind_preference(self, 'lambda_Cl36_citation', '{}.lambda_Cl36_citation'.format(prefid))
            bind_preference(self, 'lambda_Ar37_citation', '{}.lambda_Ar37_citation'.format(prefid))
            bind_preference(self, 'lambda_Ar39_citation', '{}.lambda_Ar39_citation'.format(prefid))

        except Exception:
            pass

        super(ArArConstants, self).__init__(*args, **kw)

    def _get_fixed_k3739(self):
        return self._get_ufloat('k3739')

    def _get_atm3836(self):
        return self.atm4036 / self.atm4038

    def _get_ufloat(self, attr):
        v = getattr(self, '{}_v'.format(attr))
        e = getattr(self, '{}_e'.format(attr))
        return ufloat(v, e)

    def _get_atm4036(self):
        return self._get_ufloat('atm4036')

    def _get_atm4038(self):
        return self._get_ufloat('atm4038')

    def _get_lambda_Cl36(self):
        return self._get_ufloat('lambda_Cl36')

    def _get_lambda_Ar37(self):
        return self._get_ufloat('lambda_Ar37')

    def _get_lambda_Ar39(self):
        return self._get_ufloat('lambda_Ar39')

    def _get_lambda_b(self):
        return self._get_ufloat('lambda_b')

    def _get_lambda_e(self):
        return self._get_ufloat('lambda_e')

    def _get_lambda_k(self):
        k = self.lambda_b + self.lambda_e
        return ufloat(k.nominal_value, k.std_dev)

    def _get_age_scalar(self):
        try:
            return AGE_SCALARS[self.age_units]
        except KeyError:
            return 1

