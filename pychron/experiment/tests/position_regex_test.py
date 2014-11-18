from pychron.experiment.utilities.position_regex import XY_REGEX

__author__ = 'ross'

import unittest

reg = XY_REGEX[0]


class XYTestCase(unittest.TestCase):
    def test_single_pass(self):
        t = '1.0,2.0'
        self.assertEqual(bool(reg.match(t)), True)

    def test_single_xyz_pass(self):
        t = '1.0,2.0,3.0'
        self.assertEqual(bool(reg.match(t)), True)

    def test_double_pass(self):
        t = '1.0,2.0;3.0,4.5'
        self.assertEqual(bool(reg.match(t)), True)

    def test_double_xyz_pass(self):
        t = '1.0,2.0,4.0;3.0,4.5,5.0'
        self.assertEqual(bool(reg.match(t)), True)

    def test_double_mixed_xyz_pass(self):
        t = '1.0,2.0;3.0,4.5,5.0'
        self.assertEqual(bool(reg.match(t)), True)

    def test_trailing_comma(self):
        t = '1.0,2.0,'
        self.assertEqual(bool(reg.match(t)), False)

    def test_trailing_delim(self):
        t = '1.0,2.0;'
        self.assertEqual(bool(reg.match(t)), False)

    def test_leading_delim(self):
        t = ';1.0,2.0'
        self.assertEqual(bool(reg.match(t)), False)

    def test_single_fail1(self):
        t = '1.0,2.0s'
        self.assertEqual(bool(reg.match(t)), False)

    def test_single_fail2(self):
        t = '1.0s,2.0'
        self.assertEqual(bool(reg.match(t)), False)

    def test_single_fail3(self):
        t = 's1.0,2.0'
        self.assertEqual(bool(reg.match(t)), False)

    def test_single_fail4(self):
        t = 's1.0s,s2.0s'
        self.assertEqual(bool(reg.match(t)), False)


if __name__ == '__main__':
    unittest.main()
