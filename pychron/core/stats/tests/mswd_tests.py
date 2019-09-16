from pychron.core.stats import calculate_mswd_probability

__author__ = 'ross'

import unittest


class MSWDTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_prod_even(self):
        p = calculate_mswd_probability(1, 10)
        self.assertAlmostEqual(p, 0.440493285, places=9)

    def test_prod_odd(self):
        p = calculate_mswd_probability(1, 11)
        self.assertAlmostEqual(p, 0.443263278, places=9)


if __name__ == '__main__':
    unittest.main()
