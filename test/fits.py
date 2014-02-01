from pychron.core.ui import set_toolkit
set_toolkit('qt4')
from pychron.core.helpers.fits import convert_fit
from pychron.processing.isotope import Isotope

__author__ = 'ross'

import unittest


class FitTestCase(unittest.TestCase):
    def test_convert_linear(self):
        fit='linear'
        ofit,err=convert_fit(fit)
        self.assertEqual(ofit,1)
        self.assertEqual(err,None)

    def test_convert_linear_werr(self):
        fit = 'linear_SEM'
        ofit, err = convert_fit(fit)
        self.assertEqual(ofit, 1)
        self.assertEqual(err, 'SEM')

    def test_convert_parabolic(self):
        fit = 'parabolic_CI'
        ofit, err = convert_fit(fit)
        self.assertEqual(ofit, 2)
        self.assertEqual(err, 'CI')

    def test_convert_parabolic_werr(self):
        fit = 'parabolic_SD'
        ofit, err = convert_fit(fit)
        self.assertEqual(ofit, 2)
        self.assertEqual(err, 'SD')

    def test_convert_linear_fail(self):
        fit = 'linaer'
        ofit, err = convert_fit(fit)
        self.assertEqual(ofit, None)
        self.assertEqual(err, None)

    def test_convert_average(self):
        fit = 'average'
        ofit, err = convert_fit(fit)
        self.assertEqual(ofit, 'average')
        self.assertEqual(err, 'SD')

    def test_convert_average_werr(self):
        fit = 'linear_SEM'
        ofit, err = convert_fit(fit)
        self.assertEqual(ofit, 1)
        self.assertEqual(err, 'SEM')

class FitBlockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fits= ('Ar41:(,10,average), (10,,cubic)',
                   'Ar40:parabolic',
                   'Ar39AX:parabolic',
                   'Ar39CDD:parabolic',
                   'Ar38:linear',
                   'Ar37:linear',
                   'Ar36:parabolic')

    def testAr41Fit(self):
        iso=Isotope()

        fits = dict([f.split(':') for f in self.fits])

        iso.set_fit_blocks(fits['Ar41'])
        self.assertEqual(iso.get_fit(0), 'avherage')
        self.assertEqual(iso.get_fit(-1), 'cubic')
        self.assertEqual(iso.get_fit(100), 'cubic')

if __name__ == '__main__':
    unittest.main()
