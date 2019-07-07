import unittest

from pychron.core.helpers.strtools import camel_case, ratio


class CamelCaseTestCase(unittest.TestCase):
    def setUp(self):
        self.expected = 'AbqVolc'

    def test_already_camelcase(self):
        n = self.expected
        cn = camel_case(n)
        self.assertEqual(n, cn)

    def test_underscore(self):
        n = 'abq_volc'
        cn = camel_case(n)
        self.assertEqual(self.expected, cn)

    def test_space(self):
        n = 'abq volc'
        cn = camel_case(n)
        self.assertEqual(self.expected, cn)

    def test_slash(self):
        n = 'abq/volc'
        cn = camel_case(n)
        self.assertEqual(self.expected, cn)

    def test_all_lowercase(self):
        n = 'abqvolc'
        cn = camel_case(n)
        self.assertEqual('Abqvolc', cn)


class RatioTestCase(unittest.TestCase):
    def test_ratio1(self):
        rs = ratio(['Ar40', 'Ar39', 'Ar38'])
        self.assertListEqual(['Ar40/Ar39', 'Ar40/Ar38', 'Ar39/Ar38'], rs)
