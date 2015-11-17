__author__ = 'ross'

import unittest
from pychron.stage.calibration.add_holes_view import parse_holestr


class HolesTestCase(unittest.TestCase):
    def test_s1(self):
        s1 = '1-5'
        list1 = [1, 2, 3, 4, 5]
        list2 = parse_holestr(s1)

        self.assertListEqual(list1, list2)

    def test_s2(self):
        s1 = '1,2,3'
        list1 = [1, 2, 3]
        list2 = parse_holestr(s1)

        self.assertListEqual(list1, list2)

    def test_s3(self):
        s1 = '1 -5, 7-10'
        list1 = [1, 2, 3, 4, 5, 7, 8, 9, 10]
        list2 = parse_holestr(s1)

        self.assertListEqual(list1, list2)

    def test_fail1(self):
        s1 = '1,'
        self.assertIsNone(parse_holestr(s1))

    def test_fail2(self):
        s1 = '1-5,'
        self.assertIsNone(parse_holestr(s1))

    def test_fail3(self):
        s1 = '1-,'
        self.assertIsNone(parse_holestr(s1))

    def test_fail4(self):
        s1 = '-5'
        self.assertIsNone(parse_holestr(s1))

    def test_fail5(self):
        s1 = '1-55-100'
        self.assertIsNone(parse_holestr(s1))

if __name__ == '__main__':
    unittest.main()
