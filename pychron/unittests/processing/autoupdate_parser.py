import os

__author__ = 'ross'

import unittest

from pychron.ui import set_toolkit

set_toolkit('qt4')

from pychron.processing.autoupdate_parser import AutoupdateParser


class AutoUpdateParserTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = '../data/autoupdate_AF_72'
        cls._path = p
        cls.parser = AutoupdateParser()

    def setUp(self):
        self.parser.parse(self._path)

    def test_ar40(self):
        p = self.parser
        s = p.samples['AF-72']
        self.assertEqual(s.analyses[0].Ar40, 2.210431)

    def test_nsamples(self):
        self.assertEqual(len(self.parser.samples), 1)

    def test_isFile(self):
        self.assertTrue(os.path.isfile(self._path))


if __name__ == '__main__':
    unittest.main()
