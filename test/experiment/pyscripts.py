from pychron.core.ui import set_qt

set_qt()

from pychron.pyscripts.measurement_pyscript import MeasurementPyScript

__author__ = 'ross'

import unittest


class InterpolationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = MeasurementPyScript()
        cls.script.bootstrap()
        # p=os.path.join(os.path.os.path.dirname(__file__),'data/script_options.yaml')
        p = '../data/script_options.yaml'
        cls.script.interpolation_path = p

    def test_warm_cdd(self):
        v = self.script.interpolate('warm_cdd')
        self.assertEqual(v, False)

    def test_float(self):
        v = self.script.interpolate('float_value')
        self.assertIsInstance(v, float)

    def test_fail_attr(self):
        v = self.script.interpolate('novalue')
        self.assertIsNone(v)

    def test_execute_snippet(self):
        snippet = '''def main(): a= float_valued+2'''
        v = self.script.execute_snippet(snippet)
        self.assertIs(v, None)

        snippet = '''def main(): a= float_value+boo*bat'''
        v = self.script.execute_snippet(snippet)
        self.assertIs(v, None)

    def test_execute_snippet_fail(self):
        snippet = '''def main(): a= float_valufe+2'''
        v = self.script.execute_snippet(snippet)
        self.assertIsInstance(v, str)


if __name__ == '__main__':
    unittest.main()
