from pychron.core.ui import set_qt

set_qt()

__author__ = 'ross'

import unittest
import os
from pychron.pyscripts.measurement_pyscript import MeasurementPyScript
from pychron.pyscripts.pyscript import CTXObject


class DocstrContextTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = MeasurementPyScript()
        p = 'pychron/pyscripts/tests/data/measurement_script.txt'
        if not os.path.isfile(p):
            p = './data/measurement_script.txt'

        with open(p, 'r') as fp:
            cls.script.text = fp.read()

        cls.script.bootstrap()
        cls.script.setup_context()

    def test_mx(self):
        self.assertIsInstance(self.script._ctx['mx'], CTXObject)

    def test_mx_counts(self):
        self.assertEqual(self.script._ctx['mx'].counts, 5)


class InterpolationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = MeasurementPyScript()
        cls.script.bootstrap()
        p = 'pychron/pyscripts/tests/data/script_options.yaml'
        if not os.path.isfile(p):
            p = './data/script_options.yaml'
        cls.script.interpolation_path = p

    def test_warm_cdd(self):
        v = self.script.warm_cdd
        self.assertEqual(v, False)

    def test_float(self):
        v = self.script.float_value
        self.assertIsInstance(v, float)

    def test_fail_attr(self):
        # v = self.script.novalue
        # self.assertIsNone(v)
        self.assertRaises(AttributeError, lambda: self.script.novalue)

    def test_execute_snippet(self):
        snippet = '''def main(): a= float_value+2'''
        v = self.script.execute_snippet(snippet)
        self.assertIs(v, None)

        # snippet = '''def main(): a= float_value+boo*bat'''
        # v = self.script.execute_snippet(snippet)
        # self.assertIs(v, None)

    def test_execute_snippet_fail(self):
        snippet = '''def main(): a= float_valufe+2'''
        v = self.script.execute_snippet(snippet)
        self.assertIsInstance(v, str)


if __name__ == '__main__':
    unittest.main()
