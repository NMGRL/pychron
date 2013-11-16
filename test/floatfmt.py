__author__ = 'ross'

import unittest

from pychron.ui import set_toolkit

set_toolkit('qt4')

from pychron.helpers.formatting import floatfmt

from logging import getLogger

logger = getLogger('arar_diff')


class FloatfmtTestCase(unittest.TestCase):
    def test_thousands(self):
        x = 4321.1234
        fx = floatfmt(x)
        self.assertEqual(fx, '4.32E+03')

    def test_hundreds(self):
        x = 321.1234
        fx = floatfmt(x)
        self.assertEqual(fx, '321.1234')

    def test_truncate(self):
        x = 321.123456789
        fx = floatfmt(x)
        self.assertEqual(fx, '321.1235')

    def test_hundreths(self):
        x = 0.01
        fx = floatfmt(x)
        self.assertEqual(fx, '0.0100')

        fx = floatfmt(x, n=2)
        self.assertEqual(fx, '0.01')

    def test_convert_to_scientific(self):
        x = 0.001
        fx = floatfmt(x, n=2)
        self.assertEqual(fx, '1.00E-03')

        fx = floatfmt(x, n=2, s=1)
        self.assertEqual(fx, '1.0E-03')

        x = 0.001
        fx = floatfmt(x)
        self.assertEqual(fx, '0.0010')