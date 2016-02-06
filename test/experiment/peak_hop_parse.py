from pychron.core.helpers.filetools import fileiter
from pychron.experiment.automated_run.hop_util import parse_hops, generate_hops

__author__ = 'ross'

import unittest

HOPS = [('Ar40:H1, Ar36:CDD', 2, 1),
        ('bs:39.5:H1', 45, 2),
        ('Ar39:CDD', 2, 1)]


class PeakHopCase(unittest.TestCase):
    def setUp(self):
        p = '../data/hop.txt'
        with open(p, 'r') as rfile:
            # lines=filetolist(fp)
            # lines = fileiter(fp)
            hops = [eval(li) for li in fileiter(rfile)]
            # hops = [eval(line) for line in fp if line.strip() and not line.strip().startswith('#')]
            self.gen = parse_hops(hops)

            # self.gen = parse_hops(HOPS)

    def test_parse_hop1(self):
        hop = self.gen.next()
        self.assertEqual(hop[0], False)
        self.assertEqual(hop[1], 'Ar40')
        self.assertEqual(hop[2], 'H1')

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
        self.assertEqual(h1[1], (False, False))

        h1 = g.next()
        print h1
        self.assertEqual(h1[1], (True,))

        h1 = g.next()
        print h1
        h1 = g.next()
        print h1
        self.assertEqual(h1[1], (False,))
        h1 = g.next()
        print h1
        h1 = g.next()
        print h1
        self.assertEqual(h1[1], (False, False))
        h1 = g.next()
        print h1
        self.assertEqual(h1[1], (True,))


if __name__ == '__main__':
    unittest.main()
