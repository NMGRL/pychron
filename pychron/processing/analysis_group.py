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
from traits.api import HasTraits, List, Property, cached_property, Str, Bool
#============= standard library imports ========================
from numpy import array
#============= local library imports  ==========================
from uncertainties import ufloat
from pychron.processing.analysis import Marker
from pychron.processing.argon_calculations import calculate_plateau_age, age_equation, calculate_isochron
from pychron.pychron_constants import ALPHAS
from pychron.stats.core import calculate_mswd, calculate_weighted_mean

def AGProperty():
    return Property(depends_on='analyses:[status,temp_status]')

class AnalysisGroup(HasTraits):
    sample = Str
    analyses = List
    nanalyses = AGProperty()
    arith_age = AGProperty()
    weighted_age = AGProperty()
    weighted_kca = AGProperty()
    mswd = AGProperty()

    isochron_age= AGProperty()
    identifier = Property

    #    def _calculate_weighted_mean(self, attr):
    #        vs = array([getattr(ai, attr) for ai in self.analyses
    #                    if ai.status == 0 and ai.temp_status == 0])
    #        return vs.mean()
    @cached_property
    def _get_mswd(self):
        m = ''
        args = self._get_values('uage')
        if args:
            vs, es = args
            m = calculate_mswd(vs, es)

        return m


    @cached_property
    def _get_isochron_age(self):
        return self._calculate_isochron_age()

    @cached_property
    def _get_identifier(self):
        return self.analyses[0].labnumber

    @cached_property
    def _get_weighted_age(self):
        return self._calculate_weighted_mean('uage')

    @cached_property
    def _get_weighted_kca(self):
        return self._calculate_weighted_mean('kca')

    @cached_property
    def _get_arith_age(self):
        return self._calculate_arithmetic_mean('uage')

    @cached_property
    def _get_nanalyses(self):
        return len([ai for ai in self.analyses
                    if ai.temp_status == 0 and not ai.tag])

    def _get_values(self, attr):
        vs = (getattr(ai, attr) for ai in self.analyses
              if not isinstance(ai, Marker) and \
                 ai.temp_status == 0 and not ai.tag)

        vs = [vi for vi in vs if vi is not None]
        if vs:
            vs, es = zip(*[(v.nominal_value, v.std_dev) for v in vs])
            vs, es = array(vs), array(es)
            return vs, es

    def _calculate_mean(self, attr, use_weights=True):
        args = self._get_values(attr)
        if args:
            vs, es = args
            if use_weights:
                av, werr = calculate_weighted_mean(vs, es)
            else:
                av = vs.mean()
                werr = vs.std(ddof=1)


                #if use_weights:
                #    weights = 1 / es ** 2
                #else:
                #    weights = ones(vs.shape)

                #av, sum_weights = average(vs, weights=weights, returned=True)
                #if use_weights:
                #    werr = sum_weights ** -0.5
                #else:
                #    werr = vs.std(ddof=1)
        else:
            av, werr = 0, 0

        return ufloat(av, werr)

    def _calculate_arithmetic_mean(self, attr):
        return self._calculate_mean(attr, use_weights=False)

    def _calculate_weighted_mean(self, attr):
        return self._calculate_mean(attr, use_weights=True)

    def _calculate_isochron_age(self):
        args=calculate_isochron(self.analyses)
        if args:
            return args[0]


class StepHeatAnalysisGroup(AnalysisGroup):
    plateau_age = AGProperty()
    integrated_age=AGProperty()

    plateau_steps_str=Str
    plateau_steps=None

    def calculate_plateau(self):
        return self.plateau_age

    @cached_property
    def _get_integrated_age(self):
        rad40, k39 = zip(*[(a.get_computed_value('rad40'),
                            a.get_computed_value('k39')) for a in self.analyses])
        rad40 = sum(rad40)
        k39 = sum(k39)

        j = a.j
        return age_equation(rad40 / k39, j, a.arar_constants)

    def _get_steps(self):
        d = [(ai.age,
              ai.age_err_wo_j,
              ai.isotopes['Ar39'].get_interference_corrected_value().nominal_value)
             for ai in self.analyses]

        return zip(*d)

    @cached_property
    def _get_plateau_age(self):
        ages, errors, k39=self._get_steps()
        args=calculate_plateau_age(ages, errors, k39)
        if args:
            v, e, pidx =args

            self.plateau_steps=pidx
            self.plateau_steps_str='{}-{}'.format(ALPHAS[pidx[0]],
                                                  ALPHAS[pidx[1]])
            return ufloat(v,e)


class InterpretedAge(StepHeatAnalysisGroup):
    preferred_age=Property(depends_on='preferred_age_kind')
    preferred_age_value=Property(depends_on='preferred_age_kind')
    preferred_age_error=Property(depends_on='preferred_age_kind')

    preferred_age_kind=Str
    preferred_ages= Property(depends_on='analyses')
    use=Bool

    def _get_preferred_age_value(self):
        pa=self.preferred_age
        if pa is not None:
            return pa.nominal_value

    def _get_preferred_age_error(self):
        pa = self.preferred_age
        if pa is not None:
            return pa.std_dev
    def _get_preferred_age(self):
        pa=None
        if self.preferred_age_kind=='Weighted Mean':
            pa=self.weighted_age
        elif self.preferred_age_kind=='Arthimetic Mean':
            pa=self.arith_age
        elif self.preferred_age_kind=='Isochron':
            pa=self.isochron_age
        elif self.preferred_age_kind=='Integrated':
            pa=self.integrated_age
        elif self.preferred_age_kind=='Plateau':
            pa=self.plateau_age

        return pa

    @cached_property
    def _get_preferred_ages(self):
        ps=['Weighted Mean','Arithmetic Mean','Isochron']
        if self.analyses:
            ref=self.analyses[0]
            if ref.step:
                ps.append('Integrated')
                if self.plateau_age:
                    ps.append('Plateau')

        return ps

#============= EOF =============================================

#class AnalysisRatioMean(AnalysisGroup):
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
#class AnalysisIntensityMean(AnalysisGroup):
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

