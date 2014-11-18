from pychron.processing.ratio import Ratio

__author__ = 'ross'

import unittest


class RatioTestCase(unittest.TestCase):
    def test_nom(self):
        r = Ratio(1, 2)
        self.assertEqual(r.nom.value.nominal_value, 1)

    def test_den(self):
        r = Ratio(1, 2)
        self.assertEqual(r.den.value.nominal_value, 2)

    def test_tuple1(self):
        r = Ratio((1, 0.1), (2, 0.2))
        self.assertEqual(r.value.nominal_value, 0.5)

    def test_tuple2(self):
        r = Ratio(1, (2, 0.2))
        self.assertEqual(r.value.nominal_value, 0.5)

    def test_int_value(self):
        r = Ratio(1, 2)
        self.assertEqual(r.value, 0.5)

    def test_float_value(self):
        r = Ratio(1, 2)
        self.assertEqual(r.value, 0.5)


if __name__ == '__main__':
    unittest.main()
