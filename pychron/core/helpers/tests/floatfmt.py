__author__ = 'ross'

import unittest
from pychron.core.helpers.formatting import floatfmt

DEBUG = True

class FloatfmtTestCase(unittest.TestCase):
    def test_rounding(self):
        x=0.007
        fx = floatfmt(x, n=2)
        self.assertEqual('0.01', fx)

    def test_rounding2(self):
        x=0.007
        fx = floatfmt(x, n=2)
        self.assertEqual('0.01', fx)

    @unittest.skipIf(DEBUG, 'debugging')
    def test_thousands(self):
        x = 4321.1234
        fx = floatfmt(x, s=2, use_scientific=True)
        # self.assertEqual(fx, '4.32E+03')
        self.assertEqual('4.32E+03', fx)

    @unittest.skipIf(DEBUG, 'debugging')
    def test_hundreds(self):
        x = 321.1234
        fx = floatfmt(x)
        self.assertEqual(fx, '321.1234')

    @unittest.skipIf(DEBUG, 'debugging')
    def test_truncate(self):
        x = 321.123456789
        fx = floatfmt(x)
        self.assertEqual(fx, '321.1235')

    @unittest.skipIf(DEBUG, 'debugging')
    def test_hundreths(self):
        x = 0.01
        fx = floatfmt(x)
        self.assertEqual(fx, '0.0100')

        fx = floatfmt(x, n=2)
        self.assertEqual(fx, '0.01')

    @unittest.skipIf(DEBUG, 'debugging')
    def test_convert_to_scientific1(self):
        x = 0.001
        fx = floatfmt(x, n=2, s=2, use_scientific=True)
        self.assertEqual('1.00E-03', fx)

    @unittest.skipIf(DEBUG, 'debugging')
    def test_convert_to_scientific2(self):
        x = 0.001
        fx = floatfmt(x, n=2, s=1, use_scientific=True)
        self.assertEqual('1.0E-03', fx)

    @unittest.skipIf(DEBUG, 'debugging')
    def test_convert_to_scientific3(self):
        x = 0.001
        fx = floatfmt(x)
        self.assertEqual('0.0010', fx)

