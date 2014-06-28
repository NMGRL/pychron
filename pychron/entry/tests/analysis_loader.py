from datetime import datetime
import os

__author__ = 'ross'
from pychron.core.ui import set_qt

set_qt()

import unittest
from pychron.entry.loaders.analysis_loader import XLSAnalysisLoader


class XLSAnalysisLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = XLSAnalysisLoader()
        p = 'pychron/entry/tests/data/analysis_import.xls'
        if not os.path.isfile(p):
            p = './data/analysis_import.xls'
        cls.loader.load_analyses(p)

    def test_identifier1(self):
        self._test_attr(0, 'get_identifier', '12345')

    def test_identifier2(self):
        self._test_attr(1, 'get_identifier', '12346')

    def test_project(self):
        self._test_attr(0, 'get_project', 'foo')

    def test_sample(self):
        self._test_attr(0, 'get_sample', 'bar')

    def test_material(self):
        self._test_attr(0, 'get_material', 'bat')

    def test_aliquot(self):
        self._test_attr(0, 'get_aliquot', 1)

    def test_step(self):
        self._test_attr(0, 'get_step', 'A')

    def test_analysis_time(self):
        self._test_attr(0, 'get_analysis_time', datetime(2012, 6, 7, 0, 0))

    def test_ar401(self):
        v = self.loader.get_isotope(0, 'Ar40')
        self.assertEqual(v, 'Sheet2')

    def test_ar402(self):
        v = self.loader.get_isotope(1, 'Ar40')
        self.assertEqual(v, 10)

    # def test_ar401_raw(self):
    # xs, ys = self.loader.get_isotope_data(0, 'Ar40')
    #     self.assertListEqual(xs, [1, 2, 3, 4, 5])
    #     self.assertListEqual(ys, [499, 498, 497, 496, 495])

    def test_ar402_raw(self):
        xs, ys = self.loader.get_isotope_data(1, 'Ar40')
        self.assertListEqual(xs, [])
        self.assertListEqual(ys, [])
    #
    # def test_ar391_raw(self):
    #     xs, ys = self.loader.get_isotope_data(0, 'Ar39')
    #     self.assertListEqual(xs, [1, 2, 3, 4, 5])
    #     self.assertListEqual(ys, [49, 48, 47, 46, 45])

    def _test_attr(self, idx, funcname, value):
        func = getattr(self.loader, funcname)
        self.assertEqual(func(idx), value)


if __name__ == '__main__':
    unittest.main()
