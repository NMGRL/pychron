from pychron.core.helpers.strtools import camel_case

__author__ = 'ross'

import unittest


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
