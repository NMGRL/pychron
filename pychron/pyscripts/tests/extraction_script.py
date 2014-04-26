from pychron.core.ui import set_qt

set_qt()
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript

__author__ = 'ross'

import unittest


class ExtractionTestCase(unittest.TestCase):
    def setUp(self):
        self.s = ExtractionPyScript()
        self.s.root = '.'
        self.s.name = 'co2_v2.py'
        self.s.bootstrap()
        self.s.setup_context(analysis_type='blank',
                             cleanup=1, extract_value=1, duration=1)

    def test_something(self):
        ret = self.s.execute()
        self.assertEqual(ret, True)


if __name__ == '__main__':
    unittest.main()
