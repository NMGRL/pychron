import math

from pychron.core.helpers.logger_setup import logging_setup


__author__ = 'ross'

import unittest

from pychron.core.ui import set_toolkit

set_toolkit('qt4')

from pychron.processing.autoupdate_parser import AutoupdateParser
from test.database import isotope_manager_factory

ISOTOPE_MANAGER = isotope_manager_factory(name='pychrondata_minnabluff')
ISOTOPE_MANAGER.connect()

SKIP_BLANKS = False, 'skip blanks'
SKIP_SIGNALS = False, 'skip signals'
SKIP_FITS = False, 'skip fits'

logging_setup('arar_diff')


class MassSpecPychronIsotopeTestCase(object):
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

        # cnt=7
        # if ev<1:
        #    cnt = max(1,int(abs(math.log(ev)))-2)
        #else:
        #    cnt=len(str(ev).split('.')[1])
        #logger.info('{} {}'.format(k, cnt))
        return ev, cnt

    # def test_aliquot(self):
    # a = self.analysis.aliquot
    #     self.assertEqual(a, 2)

    # age
    def test_age(self):
        v = self.analysis.age
        self._almost_equal(v, 'age')

    def test_j(self):
        v = self.analysis.j.nominal_value
        self._almost_equal(v, 'j')

    def test_j_err(self):
        v = self.analysis.j.std_dev
        self._almost_equal(v, 'j_err')

    def test_lambda_K_beta(self):
        v = self.analysis.arar_constants.lambda_b_v
        self._almost_equal(v, 'lambda_b_v')

    def test_lambda_K_epsilon(self):
        v = self.analysis.arar_constants.lambda_e_v
        self._almost_equal(v, 'lambda_b_e')

    # irradiation corrections
    def test_39_decay_factor(self):
        v = self.analysis.ar39decayfactor
        self._almost_equal(v, 'ar39decayfactor')

    def test_37_decay_factor(self):
        v = self.analysis.ar37decayfactor
        self._almost_equal(v, 'ar37decayfactor')

    def test_ca3937(self):
        v = self.analysis.interference_corrections['ca3937'].nominal_value
        self._almost_equal(v, 'ca3937')

    def test_ca3837(self):
        v = self.analysis.interference_corrections['ca3837'].nominal_value
        self._almost_equal(v, 'ca3837')

    def test_ca3637(self):
        v = self.analysis.interference_corrections['ca3637'].nominal_value
        self._almost_equal(v, 'ca3637')

    def test_k3839(self):
        v = self.analysis.interference_corrections['k3839'].nominal_value
        self._almost_equal(v, 'k3839')

    def test_k3739(self):
        v = self.analysis.interference_corrections['k3739'].nominal_value
        self._almost_equal(0, 'k3739')

    def test_k4039(self):
        v = self.analysis.interference_corrections['k4039'].nominal_value
        self._almost_equal(v, 'k4039')

    def test_cl3638(self):
        v = self.analysis.interference_corrections['cl3638'].nominal_value
        self._almost_equal(v, 'cl3638')

    # ======= fits
    @unittest.skipIf(*SKIP_FITS)
    def test_Ar40_fit(self):
        self._test_fit('Ar40')

    @unittest.skipIf(*SKIP_FITS)
    def test_Ar39_fit(self):
        self._test_fit('Ar39')

    @unittest.skipIf(*SKIP_FITS)
    def test_Ar38_fit(self):
        self._test_fit('Ar38')

    @unittest.skipIf(*SKIP_FITS)
    def test_Ar37_fit(self):
        self._test_fit('Ar37')

    @unittest.skipIf(*SKIP_FITS)
    def test_Ar36_fit(self):
        self._test_fit('Ar36')

    def _test_fit(self, isok):

        an = self.analysis
        iso = an.isotopes[isok]

        p = self.parser
        s = p.samples[self.sample_id]
        an = s.analyses[self.analysis_id]
        ev = getattr(an, '{}_fit'.format(isok))

        self.assertEqual(iso.fit_abbreviation.lower()[0], ev.lower())

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
    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar40_err(self):
        k = 'Ar40'
        self._signal_err(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar39_err(self):
        k = 'Ar39'
        self._signal_err(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar38_err(self):
        k = 'Ar38'
        self._signal_err(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar37_err(self):
        k = 'Ar37'
        self._signal_err(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar36_err(self):
        k = 'Ar36'
        self._signal_err(k)

    # ======= signal
    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar40(self):
        k = 'Ar40'
        self._signal(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar39(self):
        k = 'Ar39'
        self._signal(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar38(self):
        k = 'Ar38'
        self._signal(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar37(self):
        k = 'Ar37'
        self._signal(k)

    @unittest.skipIf(*SKIP_SIGNALS)
    def test_Ar36(self):
        k = 'Ar36'
        self._signal(k)

    def test_Ar40_decay_corrected(self):
        self._decay_corrected('Ar40')

    def test_Ar39_decay_corrected(self):
        self._decay_corrected('Ar39')

    def test_Ar38_decay_corrected(self):
        self._decay_corrected('Ar38')

    def test_Ar36_decay_corrected(self):
        self._decay_corrected('Ar37')

    def test_Ar37_decay_corrected(self):
        self._decay_corrected('Ar36')

    # def test_Ar40_disc(self):
    #     v = self.analysis.isotopes['Ar40'].discrimination.
    #     self.assertEqual(v, )
    #
    # def test_Ar36_disc(self):
    #     v = self.analysis.isotopes['Ar36'].discrimination
    #     self.assertEqual(v, 1)

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
    @unittest.skipIf(*SKIP_BLANKS)
    def test_Ar40_blank_err(self):
        k = 'Ar40'
        self._blank_err(k)

    @unittest.skipIf(*SKIP_BLANKS)
    def test_Ar40_blank(self):
        k = 'Ar40'
        self._blank(k)

    @unittest.skipIf(*SKIP_BLANKS)
    def test_Ar39_blank(self):
        k = 'Ar39'
        self._blank(k)

    @unittest.skipIf(*SKIP_BLANKS)
    def test_Ar38_blank(self):
        k = 'Ar38'
        self._blank(k)

    @unittest.skipIf(*SKIP_BLANKS)
    def test_Ar37_blank(self):
        k = 'Ar37'
        self._blank(k)

    @unittest.skipIf(*SKIP_BLANKS)
    def test_Ar36_blank(self):
        k = 'Ar36'
        self._blank(k)

    # ===============================================
    def _signal(self, k):
        an = self.analysis
        # v = an.isotopes[k].get_interference_corrected_value()
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
        v = an.isotopes[k].get_baseline_corrected_value()
        self._almost_equal(v.nominal_value, '{}_BslnCorOnly'.format(k))

    def _baseline_corrected_err(self, k):
        an = self.analysis
        v = an.isotopes[k].get_baseline_corrected_value()
        self._almost_equal(v.std_dev, '{}_Er_BslnCorOnly'.format(k))

    def _decay_corrected(self, k):
        an = self.analysis
        v = an.isotopes[k].get_decay_corrected_value()
        self._almost_equal(v.nominal_value, '{}_DecayCor'.format(k))

    def _almost_equal(self, v, k):
        ev, cnt = self.get_expected_value(k)

        sv = str(v)
        acnt = 10000
        if 'e' in sv:
            acnt = int(math.ceil(abs(math.log10(v))))
            n, _ = sv.split('e')
            n = n.split('.')
            acnt += int(len(n))

        elif '.' in sv:
            a = sv.split('.')[-1]
            acnt = len(a)

        cnt = min(acnt, cnt)
        self.assertAlmostEqual(v, ev, cnt)
        # self.assertEqual(v, ev)


#

class MassSpecPychronMixin(object):
    @classmethod
    def setUpClass(cls):
        # cls.isotope_man = isotope_manager_factory(name='pychrondata_minnabluff')
        #cls.isotope_man.db.connect()
        man = ISOTOPE_MANAGER
        db = man.db

        # cls.sample_id = 'AF-146'
        # sid = 'MB06-826a'
        #
        # with db.session_ctx():
        #     ans, tc = db.get_sample_analyses([sid, ], ['Minna Bluff'])
        #
        #     ai = next((a for a in ans if a.aliquot==2), None)
        #     an = man.make_analysis(ai, unpack=False, calculate_age=True)
        #     cls.analysis = an

        cls.sample_id = 'AF-72'
        sid = 'MB06-674'
        with db.session_ctx():
            ans, tc = db.get_sample_analyses([sid, ], ['Minna Bluff'])

            an = man.make_analysis(ans[cls.analysis_id], unpack=True, calculate_age=True)
            # ai = next((a for a in ans if a.aliquot==2), None)
            # an = man.make_analysis(ai, unpack=False, calculate_age=True)

            cls.analysis = an

        p = '../data/autoupdate_AF_72_1.txt'
        p = '../data/autoupdate_AF_72_7.875.25.txt'
        # p = '../data/autoupdate_AF_72_7.875.txt'
        # p = '../data/autoupdate_AF_72_8.03b.txt'
        # p = '../data/autoupdate_AF_146_7.875.txt'
        cls.parser = AutoupdateParser()
        cls.parser.parse(p)


class MassSpecPychronTestCaseA(MassSpecPychronIsotopeTestCase, MassSpecPychronMixin, unittest.TestCase):
    analysis_id = 0


    # class MassSpecPychronTestCaseB(MassSpecPychronIsotopeTestCase, MassSpecPychronMixin, unittest.TestCase):
    # analysis_id = 1
    #     aliquot = 2


    # class MassSpecPychronTestCaseC(MassSpecPychronIsotopeTestCase, MassSpecPychronMixin, unittest.TestCase):
    #     analysis_id = 2
    #
    #
    # class MassSpecPychronTestCaseD(MassSpecPychronIsotopeTestCase, MassSpecPychronMixin, unittest.TestCase):
    #     analysis_id = 3