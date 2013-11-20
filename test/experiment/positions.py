from pychron.ui import set_toolkit

set_toolkit('qt4')

#from pychron.paths import paths, build_directories
#paths.build('_unittest')
#build_directories(paths)
#logging_setup('export_spec')
from pychron.experiment.automated_run.factory import generate_positions

import unittest


class PositionTestCase(unittest.TestCase):
    def test_slice(self):
        pos = '1-5'
        expected = [1, 2, 3, 4, 5]

        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)

    def test_sslice(self):
        pos = '1:7:2'
        expected = [1, 3, 5, 7]
        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)

    def test_pslice(self):
        pos = '1:5'
        expected = [1, 2, 3, 4, 5]
        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)

    def test_cslice1(self):
        pos = '1-5;9'
        expected = [1, 2, 3, 4, 5, 9]
        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)

    def test_cslice2(self):
        pos = '1-5;9-11'
        expected = [1, 2, 3, 4, 5, 9, 10, 11]
        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)

    def test_cslice3(self):
        pos = '1-5;7;9-11'
        expected = [1, 2, 3, 4, 5, 7, 9, 10, 11]
        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)

    def test_cslice4(self):
        pos = '1-5;7;9-11;13-15'
        expected = [1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 15]
        ps, set_pos = generate_positions(pos)
        self.assertEqual(expected, ps)