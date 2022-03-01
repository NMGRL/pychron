import string
import unittest

from pychron.core.utils import alphas, alpha_to_int


class AlphaTestCase(unittest.TestCase):
    def test_a(self):
        self.assertEqual(alphas(0), "A")

    def test_z(self):
        self.assertEqual(alphas(25), "Z")

    def test_aa(self):
        self.assertEqual(alphas(26), "AA")

    def test_ab(self):
        self.assertEqual(alphas(27), "AB")

    def test_a_zz(self):
        ints = range(26 + 26**2)
        ass = [alphas(i) for i in ints]

        seeds = string.ascii_uppercase
        ALPHAS = [a for a in seeds] + [
            "{}{}".format(a, b) for a in seeds for b in seeds
        ]
        self.assertListEqual(ass, ALPHAS)

    def test_reciprocal(self):
        self.assertEqual(alphas(alpha_to_int("A")), "A")

    def test_reciprocal2(self):
        self.assertEqual(alphas(alpha_to_int("C")), "C")

    def test_reciprocal3(self):
        self.assertEqual(alphas(alpha_to_int("AA")), "AA")

    def test_reciprocal4(self):
        self.assertEqual(alphas(alpha_to_int("BA")), "BA")

    def test_reciprocal5(self):
        self.assertEqual(alphas(alpha_to_int("AAA")), "AAA")

    def test_reciprocal6(self):
        self.assertEqual(alphas(alpha_to_int("ZZZZ")), "ZZZZ")


if __name__ == "__main__":
    unittest.main()
