from pychron.regression.new_york_regressor import ReedYorkRegressor

__author__ = 'ross'

import unittest

from pychron.unittests.processing.standard_data import pearson


class IsochronTestCase(unittest.TestCase):
    def setUp(self):
        xs, ys, wxs, wys = pearson()

        exs = wxs ** -0.5
        eys = wys ** -0.5

        self.reg = ReedYorkRegressor(xs=xs, ys=ys,
                                     xserr=exs,
                                     yserr=eys)
        self.reg.calculate()

    def test_slope(self):
        exp = pearson('reed')
        self.assertAlmostEqual(self.reg.slope, exp['slope'], 4)

    def test_y_intercept(self):
        expected = pearson('reed')
        self.assertAlmostEqual(self.reg.intercept, expected['intercept'], 4)

    def test_x_intercept(self):
        pass
        #self.assertEqual(True, False)

    def test_age(self):
        pass

    def test_mswd(self):
        expected = pearson('reed')
        self.assertAlmostEqual(self.reg.mswd, expected['mswd'], 4)


if __name__ == '__main__':
    unittest.main()
