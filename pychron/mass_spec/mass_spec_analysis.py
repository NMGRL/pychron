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


def get_fn(blob):
    fn = None
    if blob is not None:
        ps = blob.strip().split('\n')
        fn = len(ps)
        if fn == 1 and ps[0] == '':
            fn = 0

    return fn


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
    r3739 = 0
    Cl3839 = 0

    def _sync(self, obj):

        self.j = ufloat(0, 0)
        self.age = 0
        self.age_err = 0
        self.age_err_wo_j = 0
        self.rad40_percent = ufloat(0, 0)
        self.rad4039 = ufloat(0, 0)

        arar = None
        if obj.araranalyses:
            arar = obj.araranalyses[-1]
            if arar:
                self.j = ufloat(arar.JVal, arar.JEr)
                self.age = arar.Age
                self.age_err = arar.ErrAge
                self.age_err_wo_j = arar.ErrAgeWOErInJ
                self.rad40_percent = ufloat(arar.PctRad, arar.PctRadEr)
                self.rad4039 = ufloat(arar.Rad4039, arar.Rad4039Er)
                self.r3739 = ufloat(arar.R3739Cor, arar.ErR3739Cor)
                self.Cl3839 = ufloat(arar.Cl3839, 0)
                self.kca = ufloat(arar.CaOverK, arar.CaOverKEr) ** -1
                self.kcl = ufloat(arar.ClOverK, arar.ClOverKEr) ** -1

        prefs = obj.changeable.preferences_set
        fo, fi, fs = 0, 0, 0
        if prefs:
            fo = prefs.DelOutliersAfterFit == 'true'
            fi = int(prefs.NFilterIter)
            fs = int(prefs.OutlierSigmaFactor)
            self.lambda_k = prefs.Lambda40Kepsilon + prefs.Lambda40KBeta
            self.lambda_Ar37 = prefs.LambdaAr37
            self.lambda_Ar39 = prefs.LambdaAr39
            self.lambda_Cl36 = prefs.LambdaCl36

        for dbiso in obj.isotopes:
            r = dbiso.results[-1]
            uv, ee = self._intercept_value(r)

            key = dbiso.Label
            n = dbiso.NumCnts
            det = dbiso.detector
            iso = Isotope(key, det.detector_type.Label)
            iso.baseline_corrected = ufloat(uv, ee)
            tv, te = 0, 0
            if arar:
                try:
                    k = key[2:]
                    tv, te = getattr(arar, 'Tot{}'.format(k)), getattr(arar, 'Tot{}Er'.format(k))
                except AttributeError:
                    pass

            iso.total_value = ufloat(tv, te)
            # iso.set_uvalue((uv, ee))
            iso.n = n

            iso.ic_factor = ufloat(det.ICFactor, det.ICFactorEr)

            iso.fit = r.fit.Label.lower() if r.fit else ''

            iso.baseline = Baseline(key, det.detector_type.Label)
            iso.baseline.fit = 'average'
            iso.baseline.set_filter_outliers_dict(filter_outliers=fo, iterations=fi, std_devs=fs)

            iso.baseline.n = dbiso.baseline.NumCnts

            blank = self._blank(r)
            if blank:
                iso.blank.set_uvalue(blank)

            self.isotopes[key] = iso

    def _blank(self, r):
        return r.Bkgd, r.BkgdEr

    def _intercept_value(self, r):
        """

        Iso,IsoEr is baseline/blank corrected

        Intercept,InterceptEr is only baseline corrected
        :param r:
        :return:
        """

        return r.Intercept, r.InterceptEr

    def _isotope_value(self, r):
        """
        see _intercept_value
        :param r:
        :return:
        """
        return r.Iso, r.IsoEr

    def sync_filtering(self, obj, prefs):
        """
        """
        fo, fi, fs = 0, 0, 0
        if prefs:
            fo = prefs.DelOutliersAfterFit == 'true'
            fi = int(prefs.NFilterIter)
            fs = int(prefs.OutlierSigmaFactor)
        obj.set_filter_outliers_dict(filter_outliers=fo, iterations=fi, std_devs=fs)

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

    def sync_fn(self, key, pdpblob):
        if pdpblob:
            iso = self.isotopes[key]
            fn = get_fn(pdpblob)
            if fn:
                iso.fn = iso.n - fn

    def sync_baselines(self, key, infoblob, pdpblob):
        fn = get_fn(pdpblob)
        # fn = None
        # if pdpblob is not None:
        # print 'blobl',pdpblob
        # print 'stip',pdpblob.strip()
        # print 'stip', map(ord, pdpblob.strip())
        # print 'split', pdpblob.strip().split('\n')
        # fn = len(pdpblob.strip().split('\n'))

        v, e = self._extract_average_baseline(infoblob)
        for iso in self.isotopes.itervalues():
            if iso.detector == key:
                iso.baseline.set_uvalue((v, e))
                if fn is not None:
                    iso.baseline.fn = iso.baseline.n - fn

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


class MassSpecBlank(MassSpecAnalysis):
    def _blank(self, r):
        return

    def _intercept_value(self, r):
        return r.Bkgd, r.BkgdEr

# ============= EOF =============================================
