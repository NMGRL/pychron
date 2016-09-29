import unittest

from uncertainties import nominal_value

from pychron.processing.age_converter import AgeConverter


class AgeConverterTestCase(unittest.TestCase):
    def setUp(self):
        ac = AgeConverter(n=10)
        self._ac = ac
        self._ac.setup(28.201, 5.463e-10)

    def test_age(self):
        oage = 0.7965
        oerror = 0.025
        nage = 0.7992223782

        p, e, a, b = self._ac.convert(oage, oerror)
        self.assertAlmostEqual(nage, nominal_value(p), 6)

    def test_r(self):
        age = 0.7965
        r, ex, ex_orig = self._ac._calculate_r(age)
        self.assertAlmostEqual(r, 0.0280327724, 10)

    def test_ex_unknown(self):
        age = 0.7965
        r, ex, ex_orig = self._ac._calculate_r(age)
        self.assertAlmostEqual(nominal_value(ex), 0.0004352226, 10)

    def test_ex_standard(self):
        age = 0.7965
        r, ex, ex_orig = self._ac._calculate_r(age)
        self.assertAlmostEqual(ex_orig, 0.0155254937, 10)

    def test_linear_error(self):
        oage = 0.7965
        oerror = 0.025
        nerror = 0.0250856396

        p, e, a, b = self._ac.convert(oage, oerror)
        self.assertAlmostEqual(nerror, e)


if __name__ == '__main__':
    unittest.main()
