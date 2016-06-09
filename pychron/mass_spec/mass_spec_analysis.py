# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
import StringIO
import struct

from uncertainties import ufloat
# ============= local library imports  ==========================

from pychron.processing.analyses.analysis import Analysis
from pychron.processing.isotope import Isotope, Baseline
from pychron.pychron_constants import IRRADIATION_KEYS


class Blob:
    def __init__(self, v):
        self._buf = StringIO.StringIO(v)

    def short(self):
        return struct.unpack('>h', self._buf.read(2))[0]

    def single(self):
        return struct.unpack('>f', self._buf.read(4))[0]

    def double(self):
        return struct.unpack('>d', self._buf.read(8))[0]


class MassSpecAnalysis(Analysis):
    def _sync(self, obj):

        self.j = ufloat(0, 0)
        self.age = 0
        self.age_err = 0
        self.age_err_wo_j = 0
        self.rad40_percent = ufloat(0, 0)

        if obj.araranalyses:
            arar = obj.araranalyses[-1]
            if arar:
                self.j = ufloat(arar.JVal, arar.JEr)
                self.age = arar.Age
                self.age_err = arar.ErrAge
                self.age_err_wo_j = arar.ErrAgeWOErInJ
                self.rad40_percent = ufloat(arar.PctRad, arar.PctRadEr)

        prefs = obj.changeable.preferences_set
        fo, fi, fs = 0, 0, 0
        if prefs:
            fo = prefs.DelOutliersAfterFit == 'true'
            fi = prefs.NFilterIter
            fs = prefs.OutlierSigmaFactor

        for dbiso in obj.isotopes:
            r = dbiso.results[-1]
            uv = r.Iso
            ee = r.IsoEr

            bv = r.Bkgd
            be = r.BkgdEr

            key = dbiso.Label
            n = dbiso.NumCnts
            # iso = Isotope(name=key, value=uv, error=ee, n=n)
            det = dbiso.detector
            iso = Isotope(key, det.detector_type.Label)
            iso.set_uvalue((uv, ee))
            iso.n = n

            iso.ic_factor = ufloat(det.ICFactor, det.ICFactorEr)

            iso.fit = r.fit.Label.lower() if r.fit else ''
            iso.set_filter_outliers_dict(filter_outliers=fo, iterations=fi, std_devs=fs)

            iso.baseline = Baseline(key, det.detector_type.Label)
            iso.baseline.fit = 'average'
            iso.baseline.set_filter_outliers_dict()
            iso.baseline.n = dbiso.baseline.NumCnts

            bsv = 0
            bev = 0
            iso.baseline.set_uvalue((bsv, bev))

            iso.blank.set_uvalue((bv, be))
            self.isotopes[key] = iso

    def sync_irradiation(self, irrad):
        if irrad:
            production = irrad.production
            if production:
                self.production_ratios['Ca_K'] = ufloat(production.CaOverKMultiplier,
                                                        production.CaOverKMultiplierEr)
                self.production_ratios['Cl_K'] = ufloat(production.ClOverKMultiplier,
                                                        production.ClOverKMultiplierEr)

                for k, _ in IRRADIATION_KEYS:
                    self.interference_corrections[k] = getattr(production, k.capitalize())

    def sync_baselines(self, key, infoblob):
        v, e = self._extract_average_baseline(infoblob)
        for iso in self.isotopes.itervalues():
            if iso.detector == key:
                iso.baseline.set_uvalue((v, e))

    # private
    def _extract_average_baseline(self, blob):
        mb = Blob(blob)
        n_r_pts = mb.short()
        n_pos = mb.short()
        ps = [mb.single() for i in xrange(n_pos)]

        n_seg = mb.short()
        seg_end = []
        params = []
        seg_err = []
        for i in xrange(n_seg):
            seg_end.append(mb.single())
            params.append([mb.double() for i in xrange(4)])
            seg_err.append(mb.single())

        v = params[0][0]
        e = seg_err[0]

        return v, e

# ============= EOF =============================================
