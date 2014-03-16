__author__ = 'ross'

import unittest

from numpy import linspace

from pychron.processing.isotope import Isotope


class IsotopeTestCase(unittest.TestCase):
    def setUp(self):
        self.iso = Isotope()
        xs = linspace(10, 410, 400)

        c = 1000.0
        b = -2.0
        a = 0.0

        ys = a * xs * xs + b * xs + c

        self.iso.trait_set(xs=xs, ys=ys)
        self.iso.fit = 'parabolic'

    def test_value(self):
        v = self.iso.value
        self.assertEqual(v, 999.999999999995)

    def test_filtered_value(self):
        self.iso.ys[[1, 2, 3]] = [0, 1, 1]

        d = {'filter_outliers': True,
             'filter_outliers_iteration': 1,
             'filter_outliers_std_dev': 2}

        self.iso.set_filtering(d)
        v = self.iso.value
        self.assertEqual(v, 999.99999999997499)
        # self.assertEqual(v, 99)


if __name__ == '__main__':
    unittest.main()
