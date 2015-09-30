from numpy import ma

from pychron.core.filtering import filter_items, filter_ufloats, sigma_filter

__author__ = 'ross'

import unittest


class FilteringTestCase(unittest.TestCase):
    def test_or_indices(self):
        o = filter_items([1, 10, 20], '10<x or x<5')
        self.assertListEqual(o, [0, 2])

    def test_or_items(self):
        o = filter_items([1, 10, 20, 30, 2], '10<x or x<5', return_indices=False)
        self.assertListEqual(o, [1, 20, 30, 2])

    def test_ufloats(self):
        o = filter_ufloats([(1, 1), (10, 11), (20, 1)], 'x>10')
        self.assertListEqual(o, [2])

    def test_or_ufloats(self):
        o = filter_ufloats([(1, 1), (10, 11), (20, 1)], 'x>10 or error>10')
        self.assertListEqual(o, [1, 2])

    def test_and_ufloats(self):
        o = filter_ufloats([(1, 1), (10, 1), (20, 11)], 'x>10 and error>10')
        self.assertListEqual(o, [2])

    def test_or_ufloats_percent(self):
        o = filter_ufloats([(1, 1), (10, 1), (20, 11)], 'x>10 or percent_error>50')
        self.assertListEqual(o, [0, 2])

    def test_multichar_str(self):
        o = filter_ufloats([(1, 1), (10, 1), (20, 11)], 'age>10 or percent_error>50')
        self.assertListEqual(o, [0, 2])

    def test_sigma_filter_masked(self):
        x = ma.array([1, 1, 1, 1, 1, 10], mask=False)
        x.mask[5] = True
        o = sigma_filter(x, 1)
        self.assertListEqual(o, [])

    def test_sigma_filter_masked2(self):
        x = ma.array([1, 1, 1, 1, 1, 10, 11], mask=False)
        x.mask[5] = True
        o = sigma_filter(x, 1)
        self.assertListEqual(o, [6])

    def test_sigma_filter_masked3(self):
        x = ma.array([1, 1, 1, 1, 1, 10, 11], mask=False)
        x.mask[[5, 6]] = True
        o = sigma_filter(x, 1)
        self.assertListEqual(o, [])


if __name__ == '__main__':
    unittest.main()
