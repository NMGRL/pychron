from pychron.core.ui import set_toolkit

set_toolkit('qt4')

from pychron.paths import paths

paths.build('_unittest')
#build_directories(paths)

from pychron.core.helpers.logger_setup import logging_setup

logging_setup('arar')

from test.database import isotope_manager_factory

__author__ = 'ross'

import unittest


class ArArAgeCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isotope_man = isotope_manager_factory(name='pychrondata_minnabluff')
        cls.isotope_man.db.connect()

        expected_filtered_56954_01A = dict(Ar40bs_c=2.20831,
                                           Ar39bs_c=4.96090e-3,
                                           Ar38bs_c=0.0014621,
                                           Ar37bs_c=1.34848e-3,
                                           Ar36bs_c=7.40844e-3,

                                           Ar40bs=7.50865e-5,
                                           bs_fil=[44],
                                           Ar40_fil=[1, 9, 43],
                                           Ar39_fil=[11, 16],
                                           Ar40bl=0.0328504,

                                           #Ar39_Ar40=0.002255
                                           Ar39_Ar40=1 / 443.1534341,
                                           Ar39_Ar40e=0.000023

        )

        expected_nonfiltered = dict(Ar40bs_c=2.20908914,
                                    Ar39bs_c=4.96081e-3,
                                    Ar38bs_c=0.0014706,
                                    Ar37bs_c=0.001349,
                                    Ar36bs_c=0.0074384,

                                    Ar40bs=7.50865e-5,
                                    bs_fil=[],
                                    Ar40_fil=[])

        expected_filtered = dict(
            Ar40bs_c=0.159394,
            Ar40bs_ce=2.67938e-4,
            Ar39bs_c=1.58288e-2,
            Ar39bs_ce=7.9423e-5,

            Ar40bl_c=0.129651,
            Ar40bl_ce=0.003811,

            Ar40bl=0.031794,
            Ar40ble=0.0038013,

            Ar39_Ar40=0.1226,
            Ar39_Ar40e=0.0037,
            ar37df=3.348
        )
        cls.expected = expected_nonfiltered
        cls.expected = expected_filtered
        man = cls.isotope_man
        db = man.db
        with db.session_ctx():
            ans, tc = db.get_sample_analyses(['AF-72', ], ['Minna Bluff'])
            an = man.make_analysis(ans[4])

            cls.analysis = an

    def test_Ar40blank(self):
        an = self.analysis
        iso = an.isotopes['Ar40'].blank

        self.assertAlmostEqual(iso.value,
                               self.expected['Ar40bl'], 6)

    def test_Ar40blank_error(self):
        an = self.analysis
        iso = an.isotopes['Ar40'].blank

        self.assertAlmostEqual(iso.error,
                               self.expected['Ar40ble'], 6)


    def test_Ar40bl_e(self):
        an = self.analysis
        iso = an.isotopes['Ar40']

        self.assertAlmostEqual(iso.get_corrected_value().std_dev,
                               self.expected['Ar40bl_ce'], 6)

    def test_Ar40_e(self):
        an = self.analysis
        iso = an.isotopes['Ar40']

        self.assertAlmostEqual(iso.get_baseline_corrected_value().std_dev,
                               self.expected['Ar40bs_ce'], 6)


    def test_Ar39_e(self):
        an = self.analysis
        iso = an.isotopes['Ar39']

        self.assertAlmostEqual(iso.get_baseline_corrected_value().std_dev,
                               self.expected['Ar39bs_ce'], 6)


    def test_analysis_step(self):
        an = self.analysis
        self.assertEqual(an.step, 'E')

    def test_ar37decayfactor(self):
        an = self.analysis
        self.assertAlmostEqual(an.ar37decayfactor,
                               self.expected['ar37df'], 3)

    def test_Ar39Ar40_e(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_intensity()
        a39 = an.isotopes['Ar39'].get_intensity()#*an.ar39decayfactor

        self.assertEqual((a39 / a40).std_dev, self.expected['Ar39_Ar40e'])

    def test_Ar39Ar40_v(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_intensity()
        a39 = an.isotopes['Ar39'].get_intensity() * an.ar39decayfactor

        self.assertEqual((a39 / a40).nominal_value, self.expected['Ar39_Ar40'])

    @unittest.skip
    def test_Ar40_blank(self):
        an = self.analysis
        iso = an.isotopes['Ar40']
        self.assertEqual(iso.blank.value, self.expected['Ar40bl'])

    def test_baseline_filtering(self):
        an = self.analysis
        iso = an.isotopes['Ar40'].baseline

        self.assertEqual(iso.regressor.excludes, self.expected['bs_fil'])

    def test_Ar40_filtering(self):
        an = self.analysis
        iso = an.isotopes['Ar40']

        self.assertEqual(iso.regressor.excludes, self.expected['Ar40_fil'])

    def test_Ar39_filtering(self):
        an = self.analysis
        iso = an.isotopes['Ar39']

        self.assertEqual(iso.regressor.excludes, self.expected['Ar39_fil'])

    def test_isFiltered(self):
        an = self.analysis
        iso = an.isotopes['Ar40']
        self.assertEqual(iso.filter_outliers, True)

    def test_R_errors(self):
        an = self.analysis
        self.assertNotEqual(an.F_err, an.F_err_wo_irrad)

    def test_Multiplier_baseline(self):
        an = self.analysis
        self.assertAlmostEqual(an.isotopes['Ar40'].baseline.value,
                               self.expected['Ar40bs'], 4)

    def test_Ar40_baseline_corrected(self):
        an = self.analysis
        self.assertAlmostEqual(an.isotopes['Ar40'].get_baseline_corrected_value().nominal_value,
                               self.expected['Ar40bs_c'], 4)


    def test_Ar39_baseline_corrected(self):
        an = self.analysis
        self.assertAlmostEqual(an.isotopes['Ar39'].get_baseline_corrected_value().nominal_value,
                               self.expected['Ar39bs_c'], 7)


    def test_Ar37_baseline_corrected(self):
        an = self.analysis
        self.assertAlmostEqual(an.isotopes['Ar37'].get_baseline_corrected_value().nominal_value,
                               self.expected['Ar37bs_c'], 7)


    def test_Ar38_baseline_corrected(self):
        an = self.analysis
        self.assertAlmostEqual(an.isotopes['Ar38'].get_baseline_corrected_value().nominal_value,
                               self.expected['Ar38bs_c'], 7)

    def test_Ar36_baseline_corrected(self):
        an = self.analysis
        self.assertAlmostEqual(an.isotopes['Ar36'].get_baseline_corrected_value().nominal_value,
                               self.expected['Ar36bs_c'], 7)


    @unittest.skip
    def test_39_40(self):
        def _func(an):
            a39 = an.isotopes['Ar39'].get_interference_corrected_value()
            a40 = an.isotopes['Ar40'].get_interference_corrected_value()

            a40 = an.isotopes['Ar40'].get_intensity()
            e = a40.std_dev
            #v=(a39/a40).nominal_value
            #v=(a40/a39).nominal_value
            #e=(a40/a39).std_dev
            ##e=(a39/a40).std_dev
            #self.assertEqual(v,
            #                 self.expected_bs_corrected['Ar39_Ar40']
            #                 )
            self.assertEqual(e,
                             self.expected['Ar39_Ar40e']
            )

        self._get_analysis(_func)


if __name__ == '__main__':
    unittest.main()
