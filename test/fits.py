from pychron.core.helpers.fits import convert_fit

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

if __name__ == '__main__':
    unittest.main()
