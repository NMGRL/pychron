from pychron.core.ui import set_qt

set_qt()

from pychron.pyscripts.hops_editor import Position, Hop, HopSequence

__author__ = 'ross'

import unittest


class PositionTestCase(unittest.TestCase):
    def test_to_string_no_deflection(self):
        p = Position(detector='H1', isotope='Ar40')
        self.assertEqual(p.to_string(), 'Ar40:H1')

    def test_to_string_deflection(self):
        p = Position(detector='H1', isotope='Ar40', deflection=10)
        self.assertEqual(p.to_string(), 'Ar40:H1:10')


class HopTestCase(unittest.TestCase):
    def setUp(self):
        self.hop = Hop()

    def test_validate_hop_fail(self):
        p1 = Position(detector='H1', isotope='Ar40')
        p2 = Position(detector='H2', isotope='Ar40')
        self.hop.positions = [p1, p2]

        self.assertEqual(self.hop.validate_hop(), False)
        self.assertEqual(self.hop.error_message, 'Multiple Isotopes: Ar40')

    def test_validate_hop_fail2(self):
        p1 = Position(detector='H1', isotope='Ar40')
        p2 = Position(detector='H1', isotope='Ar39')
        self.hop.positions = [p1, p2]

        self.assertEqual(self.hop.validate_hop(), False)
        self.assertEqual(self.hop.error_message, 'Multiple Detectors: H1')

    def test_validate_hop_fail3(self):
        p1 = Position(detector='H1', isotope='Ar40')
        p2 = Position(detector='H1', isotope='Ar39')
        p3 = Position(detector='H2', isotope='Ar40')
        p4 = Position(detector='H2', isotope='Ar39')
        self.hop.positions = [p1, p2, p3, p4]

        self.assertEqual(self.hop.validate_hop(), False)
        self.assertEqual(self.hop.error_message, 'Multiple Isotopes: Ar40, Ar39; Multiple Detectors: H1, H2')

    def test_validate_hop_pass(self):
        p1 = Position(detector='H1', isotope='Ar40')
        p2 = Position(detector='H2', isotope='Ar39')
        self.hop.positions = [p1, p2]

        self.assertEqual(self.hop.validate_hop(), True)
        self.assertEqual(self.hop.error_message, '')

    def test_to_string(self):
        self.hop.counts = 10
        self.hop.settle = 3
        p1 = Position(detector='H1', isotope='Ar40')
        p2 = Position(detector='H2', isotope='Ar39')
        self.hop.positions = [p1, p2]

        self.assertEqual(self.hop.to_string(), "('Ar40:H1, Ar39:H2', 10, 3)")

    def test_parse_hopstr(self):
        hs = 'Ar40:H1:10,     Ar39:AX,     Ar36:CDD'

        self.hop.parse_hopstr(hs)
        self.assertEqual(len(self.hop.positions), 3)


class HopSequenceTestCase(unittest.TestCase):
    def setUp(self):
        hop = Hop()
        hop.counts = 10
        hop.settle = 3
        p1 = Position(detector='H1', isotope='Ar40')
        p2 = Position(detector='H2', isotope='Ar39')
        hop.positions = [p1, p2]

        hop2 = Hop()
        hop2.counts = 100
        hop2.settle = 30
        p1 = Position(detector='L1', isotope='Ar40')
        p2 = Position(detector='L2', isotope='Ar39')
        hop2.positions = [p1, p2]

        self.hop_sequence = HopSequence(hops=[hop, hop2])

    def test_to_string(self):
        s = """('Ar40:H1, Ar39:H2', 10, 3)
('Ar40:L1, Ar39:L2', 100, 30)"""
        self.assertEqual(self.hop_sequence.to_string(), s)


if __name__ == '__main__':
    unittest.main()
