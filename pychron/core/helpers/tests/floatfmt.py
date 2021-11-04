__author__ = "ross"

import unittest

from pychron.core.helpers.formatting import floatfmt, standard_sigfigsfmt

DEBUG = True


class SigFigStdFmtTestCase(unittest.TestCase):
    def test_ones(self):
        self.assertEqual(("123", "1"), standard_sigfigsfmt(123.456, 1))

    def test_tens(self):
        self.assertEqual(("123", "12"), standard_sigfigsfmt(123.456, 12.123))

    def test_tenths(self):
        self.assertEqual(("123.5", "0.1"), standard_sigfigsfmt(123.456, 0.1))

    def test_hundreths(self):
        self.assertEqual(("123.46", "0.01"), standard_sigfigsfmt(123.456, 0.01))

    def test_hundreths2(self):
        self.assertEqual(("123.46", "0.02"), standard_sigfigsfmt(123.456, 0.02))

    def test_hundreths3(self):
        self.assertEqual(("123.46", "0.08"), standard_sigfigsfmt(123.456, 0.08))


class FloatfmtTestCase(unittest.TestCase):
    def test_rounding(self):
        x = 0.007
        fx = floatfmt(x, n=2)
        self.assertEqual("0.01", fx)

    def test_rounding2(self):
        x = 0.007
        fx = floatfmt(x, n=2)
        self.assertEqual("0.01", fx)

    @unittest.skipIf(DEBUG, "debugging")
    def test_thousands(self):
        x = 4321.1234
        fx = floatfmt(x, s=2, use_scientific=True)
        # self.assertEqual(fx, '4.32E+03')
        self.assertEqual("4.32E+03", fx)

    @unittest.skipIf(DEBUG, "debugging")
    def test_hundreds(self):
        x = 321.1234
        fx = floatfmt(x)
        self.assertEqual(fx, "321.1234")

    @unittest.skipIf(DEBUG, "debugging")
    def test_truncate(self):
        x = 321.123456789
        fx = floatfmt(x)
        self.assertEqual(fx, "321.1235")

    @unittest.skipIf(DEBUG, "debugging")
    def test_hundreths(self):
        x = 0.01
        fx = floatfmt(x)
        self.assertEqual(fx, "0.0100")

        fx = floatfmt(x, n=2)
        self.assertEqual(fx, "0.01")

    @unittest.skipIf(DEBUG, "debugging")
    def test_convert_to_scientific1(self):
        x = 0.001
        fx = floatfmt(x, n=2, s=2, use_scientific=True)
        self.assertEqual("1.00E-03", fx)

    @unittest.skipIf(DEBUG, "debugging")
    def test_convert_to_scientific2(self):
        x = 0.001
        fx = floatfmt(x, n=2, s=1, use_scientific=True)
        self.assertEqual("1.0E-03", fx)

    @unittest.skipIf(DEBUG, "debugging")
    def test_convert_to_scientific3(self):
        x = 0.001
        fx = floatfmt(x)
        self.assertEqual("0.0010", fx)
