from pychron.core.stats import calculate_mswd2
from test.processing.standard_data import pearson

__author__ = 'ross'

import unittest


class MSWDTestCase(unittest.TestCase):

    def test_chi_squared(self):

        x, y, wx, wy = pearson()

        b = -0.4807
        a = 5.4806

        ex = 1 / wx ** 0.5
        ey = 1 / wy ** 0.5

        v = 1.4833
        m = calculate_mswd2(x, y, ex, ey, a, b, correlated_errors=True)
        self.assertAlmostEqual(m, v, 4)

        v = 2.2045
        m = calculate_mswd2(x, y, ex, ey, a, b)
        self.assertAlmostEqual(m, v, 4)

if __name__ == '__main__':
    unittest.main()
