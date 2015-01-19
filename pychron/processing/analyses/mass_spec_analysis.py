#===============================================================================
# Copyright 2013 Jake Ross
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

#============= standard library imports ========================
#============= local library imports  ==========================
from uncertainties import ufloat
from pychron.processing.analyses.analysis import Analysis
from pychron.processing.isotope import Isotope, Blank, Baseline
from pychron.pychron_constants import IRRADIATION_KEYS


class MassSpecAnalysis(Analysis):
    def _sync(self, obj):

        for dbiso in obj.isotopes:
            r = dbiso.results[-1]
            uv = r.Iso
            ee = r.IsoEr

            bv = r.Bkgd
            be = r.BkgdEr

            key = dbiso.Label
            n = dbiso.NumCnts
            iso = Isotope(name=key, value=uv, error=ee, n=n)
            det =dbiso.detector
            iso.ic_factor=ufloat(det.ICFactor, det.ICFactorEr)
            iso.fit = r.fit.Label.lower()

            iso.baseline = Baseline(name=key,
                                    reverse_unpack=True,
                                    dbrecord=dbiso.baseline,
                                    unpack=True,
                                    unpacker=lambda x: x.PeakTimeBlob,
                                    error_type='SEM',
                                    fit='average')
            iso.baseline.set_filter_outliers_dict()

            iso.blank = Blank(name=key, value=bv, error=be)
            self.isotopes[key] = iso

    def sync_irradiation(self, irrad):
        production = irrad.production
        self.production_ratios['Ca_K']=ufloat(production.CaOverKMultiplier,
                                              production.CaOverKMultiplierEr)
        self.production_ratios['Cl_K']=ufloat(production.ClOverKMultiplier,
                                              production.ClOverKMultiplierEr)

        for k,_ in IRRADIATION_KEYS:
            self.interference_corrections[k]=getattr(production,k.capitalize())

#============= EOF =============================================
