__author__ = 'ross'

import os

from pychron.core.ui import set_qt

set_qt()

import unittest
from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader


class XLSIrradiationLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = XLSIrradiationLoader()
        p = 'pychron/entry/tests/data/irradiation_import.xls'
        if not os.path.isfile(p):
            p = './data/irradiation_import.xls'
        # cls.loader.load_analyses(p)
        cls.loader.open(p)

    # def test_iteration2(self):
    # irrads = self.loader.iterate_irradiations2()
    # self.assertEqual(len(irrads), 2)
    #     self.assertEqual(len(irrads[0]), 6)
    #     self.assertEqual(len(irrads[1]), 5)

    def test_iteration1(self):
        irrads = self.loader.iterate_irradiations()
        irrads = list(irrads)
        self.assertEqual(len(irrads), 2)
        self.assertEqual(len(list(irrads[0])), 5)
        self.assertEqual(len(list(irrads[1])), 4)

    def test_iteration2(self):
        irrads = self.loader.iterate_irradiations()
        irrads = list(irrads)

        airrad = irrads[0]
        birrad = irrads[1]
        aheader = airrad.next()
        bheader = birrad.next()

        self.assertEqual('NM-1000', aheader[0].value)
        self.assertEqual('NM-1001', bheader[0].value)

    def test_add_irradiations(self):
        self.loader.add_irradiations()
        self.assertEqual(self.loader.added_irradiations, ['NM-1000', 'NM-1001'])

    def test_add_levels(self):
        self.loader.add_irradiations()

        self.assertEqual(self.loader.added_levels, [('NM-1000', 'A', 'Triga PR', '8-Hole'),
                                                    ('NM-1000', 'B', 'Triga PR', '8-Hole'),
                                                    ('NM-1000', 'C', 'Triga PR', '8-Hole'),
                                                    ('NM-1000', 'D', 'Triga PR', '8-Hole'),
                                                    ('NM-1000', 'E', 'Triga PR', '8-Hole'),
                                                    ('NM-1001', 'A', 'Triga PR', '8-Hole'),
                                                    ('NM-1001', 'B', 'Triga PR', '8-Hole'),
                                                    ('NM-1001', 'C', 'Triga PR', '8-Hole'),
                                                    ('NM-1001', 'D', 'Triga PR', '8-Hole')])

    def test_add_chronologies(self):
        self.loader.add_irradiations()
        # self.assertListEqual(self.loader.added_chronologies, [('NM-1000', '2012-12-12 01:01:01', 'ED', 1),
        #                                                       ('NM-1000', 'SD', 'ED', 1),
        #                                                       ('NM-1001', 'SD', 'ED', 1),
        #                                                       ('NM-1001', 'SD', 'ED', 10),])
        self.assertListEqual(self.loader.added_chronologies,
                              [('NM-1000', '2012-12-12 01:01:00', '2012-12-12 02:01:00', 1),
                               ('NM-1000', '2012-12-12 04:01:00', '2012-12-12 05:01:00', 1),
                               ('NM-1001', '2012-01-12 01:01:00', '2012-01-12 02:01:00', 1),
                               ('NM-1001', '2012-01-12 04:01:00', '2012-01-12 05:01:00', 10),
                               ])

    def test_add_positions(self):
        self.loader.add_positions()

        self.assertEqual(self.loader.added_positions[:6], [('NM-1000', 'A', 1),
                                                           ('NM-1000', 'A', 2),
                                                           ('NM-1000', 'A', 3),
                                                           ('NM-1000', 'B', 1),
                                                           ('NM-1000', 'B', 2),
                                                           ('NM-1000', 'B', 3)])

        # def test_nlevels_explicit(self):
        #     nl = self.loader.get_nlevels('NM-1000')
        #     self.assertEqual(4, nl)
        #
        # def test_nlevels_implicit(self):
        #     nl = self.loader.get_nlevels('NM-1001')
        #     self.assertEqual(5, nl)


if __name__ == '__main__':
    unittest.main()

