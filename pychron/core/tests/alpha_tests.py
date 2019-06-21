import unittest

from pychron.core.utils import alphas, alpha_to_int


class AlphaTestCase(unittest.TestCase):
    def test_a_alpha(self):
        self.assertEqual(alphas(0), 'A')

    def test_zero(self):
        self.assertEqual(alpha_to_int('A'), 0)

    def test_b_alpha(self):
        self.assertEqual(alphas(1), 'B')

    def test_one(self):
        self.assertEqual(alpha_to_int('B'), 1)

    def test_aa(self):
        self.assertEqual(alphas(26), 'AA')


if __name__ == '__main__':
    unittest.main()
