import math
import string

__author__ = 'ross'

import unittest

from pychron.ui import set_toolkit

set_toolkit('qt4')

from pychron.processing.autoupdate_parser import AutoupdateParser
from test.database import isotope_manager_factory

from logging import getLogger

logger = getLogger('arar_diff')


class MassSpecPychronTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isotope_man = isotope_manager_factory(name='pychrondata_minnabluff')
        cls.isotope_man.db.connect()
        man = cls.isotope_man
        db = man.db

        cls.sample_id = sid = 'AF-72'
        cls.analysis_id = aid = string.ascii_uppercase.index('A')

        with db.session_ctx():
            ans, tc = db.get_sample_analyses([sid, ], ['Minna Bluff'])
            an = man.make_analysis(ans[aid])

            cls.analysis = an

        p = '../data/autoupdate_AF_72_1'
        cls.parser = AutoupdateParser()
        cls.parser.parse(p)

    def setUp(self):
        pass

    def get_expected_value(self, k):
        p = self.parser

        s = p.samples[self.sample_id]
        an = s.analyses[self.analysis_id]
        ev = getattr(an, k)

        sev = str(ev)
        if '.' in sev:
            cnt = len(str(ev).split('.')[1])
        else:
            cnt = int(abs(math.log(ev, 10)))

        #cnt=7
        #if ev<1:
        #    cnt = max(1,int(abs(math.log(ev)))-2)
        #else:
        #    cnt=len(str(ev).split('.')[1])
        #logger.info('{} {}'.format(k, cnt))
        return ev, cnt

    # ======= ratios
    def test_Ar39_Ar40(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a39 = an.isotopes['Ar39'].get_interference_corrected_value()

        r = a39 / a40

        self._almost_equal(r.nominal_value, 'Isoch_39_40')

    def test_Ar39_Ar40err(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a39 = an.isotopes['Ar39'].get_interference_corrected_value()

        r = a39 / a40

        self._almost_equal(r.std_dev / r.nominal_value * 100, 'Isoch_39_40err')

    def test_Ar36_Ar40(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a36 = an.isotopes['Ar36'].get_interference_corrected_value()
        r = a36 / a40

        self._almost_equal(r.nominal_value, 'Isoch_36_40')

    def test_Ar36_Ar40err(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a36 = an.isotopes['Ar36'].get_interference_corrected_value()
        r = a36 / a40

        self._almost_equal(r.std_dev / r.nominal_value * 100, 'Isoch_36_40err')

    # ======= signal err
    def test_Ar40_err(self):
        k = 'Ar40'
        self._signal_err(k)

    def test_Ar39_err(self):
        k = 'Ar39'
        self._signal_err(k)

    def test_Ar38_err(self):
        k = 'Ar38'
        self._signal_err(k)

    def test_Ar37_err(self):
        k = 'Ar37'
        self._signal_err(k)

    def test_Ar36_err(self):
        k = 'Ar36'
        self._signal_err(k)

    # ======= signal
    def test_Ar40(self):
        k = 'Ar40'
        self._signal(k)

    def test_Ar39(self):
        k = 'Ar39'
        self._signal(k)

    def test_Ar38(self):
        k = 'Ar38'
        self._signal(k)

    def test_Ar37(self):
        k = 'Ar37'
        self._signal(k)

    def test_Ar36(self):
        k = 'Ar36'
        self._signal(k)

    # ======= baseline only
    def test_Ar40_baseline_corrected(self):
        k = 'Ar40'
        self._baseline_corrected(k)

    def test_Ar39_baseline_corrected(self):
        k = 'Ar39'
        self._baseline_corrected(k)

    def test_Ar38_baseline_corrected(self):
        k = 'Ar38'
        self._baseline_corrected(k)

    def test_Ar37_baseline_corrected(self):
        k = 'Ar37'
        self._baseline_corrected(k)

    def test_Ar36_baseline_corrected(self):
        k = 'Ar36'
        self._baseline_corrected(k)

    # ======= baseline only error
    def test_Ar40_baseline_corrected_err(self):
        k = 'Ar40'
        self._baseline_corrected_err(k)

    def test_Ar39_baseline_corrected_err(self):
        k = 'Ar39'
        self._baseline_corrected_err(k)

    def test_Ar38_baseline_corrected_err(self):
        k = 'Ar38'
        self._baseline_corrected_err(k)

    def test_Ar37_baseline_corrected_err(self):
        k = 'Ar37'
        self._baseline_corrected_err(k)

    def test_Ar36_baseline_corrected_err(self):
        k = 'Ar36'
        self._baseline_corrected_err(k)

    # ======= blanks
    def test_Ar40_blank_err(self):
        k = 'Ar40'
        self._blank_err(k)

    def test_Ar40_blank(self):
        k = 'Ar40'
        self._blank(k)

    def test_Ar39_blank(self):
        k = 'Ar39'
        self._blank(k)

    def test_Ar38_blank(self):
        k = 'Ar38'
        self._blank(k)

    def test_Ar37_blank(self):
        k = 'Ar37'
        self._blank(k)

    def test_Ar36_blank(self):
        k = 'Ar36'
        self._blank(k)

    #===============================================
    def _signal(self, k):
        an = self.analysis
        v = an.isotopes[k].get_intensity()
        self._almost_equal(v.nominal_value, k)

    def _signal_err(self, k):
        an = self.analysis
        v = an.isotopes[k].get_intensity()
        self._almost_equal(v.std_dev, '{}Er'.format(k))

    def _blank_err(self, k):
        an = self.analysis
        v = an.isotopes[k].blank.error
        self._almost_equal(v, '{}_BkgdEr'.format(k))

    def _blank(self, k):
        an = self.analysis
        v = an.isotopes[k].blank.value
        self._almost_equal(v, '{}_Bkgd'.format(k))

    def _baseline_corrected(self, k):
        an = self.analysis
        v = an.isotopes[k].baseline_corrected_value()
        self._almost_equal(v.nominal_value, '{}_BslnCorOnly'.format(k))

    def _baseline_corrected_err(self, k):
        an = self.analysis
        v = an.isotopes[k].baseline_corrected_value()
        self._almost_equal(v.std_dev, '{}_Er_BslnCorOnly'.format(k))

    def _interference_corrected(self, k):
        an = self.analysis
        v = an.isotopes[k].get_interference_corrected_value()
        self._almost_equal(v.nominal_value, '{}_DecayCor'.format(k))


    def _almost_equal(self, v, k):
        ev, cnt = self.get_expected_value(k)

        sv = str(v)
        acnt = 10000
        if 'e' in sv:
            acnt = int(round(abs(math.log10(v))))
        elif '.' in sv:
            a = sv.split('.')[-1]
            acnt = len(a)

        cnt = min(acnt, cnt)
        self.assertAlmostEqual(v, ev, cnt)
