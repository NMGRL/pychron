import yaml

from pychron.experiment.automated_run.hop_util import parse_hops, generate_hops

__author__ = 'ross'

import unittest

HOPS = [('Ar40:H1, Ar36:CDD', 2, 1),
        ('bs:39.5:H1', 45, 2),
        ('Ar39:CDD', 2, 1)]

YAML_HOP = '''
- counts: 2
  settle: 1
  cup_configuration:
   - isotope: Ar40
     active: True
     deflection: 10
     detector: H1
     protect: False
     is_baseline: False
   - isotope: Ar39
     active: True
     deflection: None
     detector: AX
     protect: False
     is_baseline: False
   - isotope: Ar36
     active: True
     deflection: None
     detector: CDD
     protect: False
     is_baseline: False
- counts: 30
  settle: 10
  cup_configuration:
   - isotope: Ar37
     active: True
     deflection: None
     detector: CDD
     protect: False
     is_baseline: False
'''


class PeakHopYamlCase(unittest.TestCase):
    def setUp(self):
        hops = yaml.load(YAML_HOP)
        self.gen = generate_hops(hops)

    def test_hop1_settle(self):
        hop = self.hop1()
        self.assertEqual(hop['settle'], 1)

    def test_hop1_counts(self):
        hop = self.hop1()
        self.assertEqual(hop['counts'], 2)

    def test_hop1_detectors(self):
        hop = self.hop1()
        self.assertEqual(hop['detectors'], ['H1', 'AX', 'CDD'])

    def test_hop1_detectors(self):
        hop = self.hop1()
        self.assertEqual(hop['isotopes'], ['Ar40', 'Ar39', 'Ar36'])

    def test_hop2_settle(self):
        hop = self.hop2()
        self.assertEqual(hop['settle'], 10)

    def test_hop2_counts(self):
        hop = self.hop2()
        self.assertEqual(hop['counts'], 30)

    def test_hop2_detectors(self):
        hop = self.hop2()
        self.assertEqual(hop['detectors'], ['CDD'])

    def test_hop2_detectors(self):
        hop = self.hop2()
        self.assertEqual(hop['isotopes'], ['Ar37'])

    def hop1(self):
        hop = next(self.gen)
        return hop

    def hop2(self):
        next(self.gen)
        next(self.gen)
        hop = next(self.gen)
        return hop


class PeakHopTxtCase(unittest.TestCase):
    def setUp(self):
        hop_txt = '''#('Ar40:H1:10,     Ar39:AX,     Ar36:CDD',      3, 1)
#('Ar40:L2,     Ar39:CDD',                   3, 1)
#('Ar38:CDD',                                3, 1)
#('Ar37:CDD',                                3, 1)
('Ar40:H1, Ar36:CDD', 2, 1)
('bs:39.5:H1', 45, 2)
('Ar39:CDD', 2, 1)'''
        lines = hop_txt.split('\n')
        hops = [eval(li) for li in lines if not li.startswith('#')]
        # hops = [eval(line) for line in fp if line.strip() and not line.strip().startswith('#')]
        self.gen = parse_hops(hops)

        # self.gen = parse_hops(HOPS)
        # p = '../data/hop.txt'
        # with open(p, 'r') as rfile:
        #     # lines=filetolist(fp)
        #     # lines = fileiter(fp)
        #     hops = [eval(li) for li in fileiter(rfile)]
        #     # hops = [eval(line) for line in fp if line.strip() and not line.strip().startswith('#')]
        #     self.gen = parse_hops(hops)
        #
        #     # self.gen = parse_hops(HOPS)

    def test_parse_hop1(self):
        hop = self.gen.next()
        self.assertEqual(hop[0], False)
        # self.assertEqual(hop[1], 'Ar40')
        # self.assertEqual(hop[2], 'H1')

    def test_parse_baseline(self):
        hop = self.gen.next()
        hop = self.gen.next()
        hop = self.gen.next()
        self.assertEqual(hop[0], True)
        self.assertEqual(hop[1], '39.5')
        self.assertEqual(hop[2], 'H1')

    def test_generate_hops(self):
        g = generate_hops(HOPS)
        h1 = g.next()
        print h1
        h1 = g.next()
        print h1
        self.assertEqual(h1['is_baselines'], (False, False))

        h1 = g.next()
        print h1
        self.assertEqual(h1['is_baselines'], (True,))

        h1 = g.next()
        print h1
        h1 = g.next()
        print h1
        self.assertEqual(h1['is_baselines'], (False,))
        h1 = g.next()
        print h1
        h1 = g.next()
        print h1
        self.assertEqual(h1['is_baselines'], (False, False))
        h1 = g.next()
        print h1
        self.assertEqual(h1['is_baselines'], (True,))


if __name__ == '__main__':
    unittest.main()
