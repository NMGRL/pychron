from pychron.stats import calculate_mswd2
from test.processing.standard_data import pearson

__author__ = 'ross'

import unittest


class MSWDTestCase(unittest.TestCase):
    def setUp(self):
        #self.x=[1,2]
        #self.y=[1,2]
        #self.ex=[1,1]
        #self.ey=[1,1]
        #=pearson()
        self.a = 1
        self.b = 1
        self.chi2 = 1

    def test_chi_squared(self):
        #x=self.x
        #y=self.y
        #ex=self.ex
        #ey=self.ey
        #a=self.a
        #b=self.b
        x, y, wx, wy = pearson()

        b = -0.4807
        a = 5.4806

        ex = 1 / wx ** 0.5
        ey = 1 / wy ** 0.5

        v = 1.4833
        m = calculate_mswd2(x, y, ex, ey, a, b)
        self.assertAlmostEqual(m, v, 4)


if __name__ == '__main__':
    unittest.main()
