__author__ = 'ross'

import os
import unittest

from pychron.core.ui import set_qt

set_qt()

from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader

TEST_PARSE_XLS = False
DEBUGGING = False

DBNAME = 'loader.db'


def get_data_dir():
    op = 'pychron/entry/tests/data'
    if not os.path.isdir(op):
        op = os.path.join('.', 'data')
    return op


def db_factory():
    from pychron.database.adapters.isotope_adapter import IsotopeAdapter
    from pychron.database.orms.isotope.util import Base

    db = IsotopeAdapter()
    db.verbose_retrieve_query = True
    db.trait_set(kind='sqlite', path=os.path.join(get_data_dir(), DBNAME))
    db.connect()

    if os.path.isfile(db.path):
        os.remove(db.path)

    metadata = Base.metadata
    db.create_all(metadata)
    with db.session_ctx() as sess:
        metadata.create_all(sess.bind)

    return db


class XLSIrradiationLoaderLoadTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = XLSIrradiationLoader()
        p = os.path.join(get_data_dir(), 'irradiation_import.xls')
        cls.input_path = p

    def setUp(self):
        self.loader.open(self.input_path)
        # rebuild the local db
        self.loader.db = db_factory()

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_irradiation_dry(self):
        self.loader.add_irradiation('NM-1000', dry=True)
        obj = self.loader.db.get_irradiation('NM-1000')
        self.assertIsNone(obj)

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_irradiation(self):
        self.loader.add_irradiation('NM-1000')
        with self.loader.db.session_ctx():
            obj = self.loader.db.get_irradiation('NM-1000')
            self.assertEqual(obj.name, 'NM-1000')

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_level_dry(self):
        self.loader.add_irradiation('NM-1000')
        self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1, dry=True)
        obj = self.loader.db.get_irradiation_level('NM-1000', 'A')
        self.assertIsNone(obj)

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_level(self):
        self.loader.add_irradiation('NM-1000')
        self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1)
        with self.loader.db.session_ctx():
            obj = self.loader.db.get_irradiation_level('NM-1000', 'A')
            self.assertTupleEqual((obj.irradiation.name, obj.name),
                                  ('NM-1000', 'A'))

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_position_dry(self):
        self.loader.add_irradiation('NM-1000')
        self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1)
        pdict = {'irradiation': 'NM-1000',
                 'level': 'A',
                 'position': 1,
                 'material': 'sanidine',
                 'sample': 'FC-2',
                 'is_monitor': True,
                 'weight': 100,
                 'note': 'this is a note'}

        self.loader.add_position(pdict, dry=True)
        obj = self.loader.db.get_irradiation_position('NM-1000', 'A', 1)
        self.assertIsNone(obj)

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_position(self):
        self.loader.add_irradiation('NM-1000')
        self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1)
        pdict = {'irradiation': 'NM-1000',
                 'level': 'A',
                 'position': 1,
                 'material': 'sanidine',
                 'sample': 'FC-2',
                 'is_monitor': True,
                 'weight': 100,
                 'note': 'this is a note'}

        self.loader.add_position(pdict)
        with self.loader.db.session_ctx():
            obj = self.loader.db.get_irradiation_position('NM-1000', 'A', 1)
            self.assertTupleEqual((obj.position, obj.level.name, obj.level.irradiation.name),
                                  (1, 'A', 'NM-1000'))


    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_generate_offsets1(self):
        # fool loader into thinking 1 irradiation and 1 level were added
        self.loader._added_irradiations = [0]
        self.loader._added_levels = [0]

        io, lo = self.loader.update_offsets()
        self.assertTupleEqual((io, lo), (100,0))

    # @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_generate_labnumber(self):
        # add a placeholder labnumber

        self.loader.db.add_labnumber(1000, 'FC-2')

        # fool loader into thinking 1 irradiation and 1 level were added
        self.loader._added_irradiations = [0]
        self.loader._added_levels = [0]

        gen = self.loader.identifier_generator()

        self.assertEqual((gen.next(), gen.next()), (1100,1101))

    # def test_generate_offsets2(self):
    #     # fool loader into thinking 2 irradiations and 8 level were added (4 to each irradiation)
    #     self.loader._added_irradiations = [0,1]
    #     self.loader._added_levels = [0,0,0,0,1,1,1,1]
    #
    #     io, lo = self.loader.update_offsets()
    #     self.assertTupleEqual((io, lo), (200, 0))

        # idn2 = self.loader.next_identifier()

        # self.assertTupleEqual((idn1,idn2), (1100, 1110))

        # self.loader.autogenerate_labnumber = True
        # self.loader.add_irradiation('NM-1000')
        # self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1)
        # pdict = {'irradiation': 'NM-1000',
        #          'level': 'A',
        #          'position': 1,
        #          'material': 'sanidine',
        #          'sample': 'FC-2',
        #          'is_monitor': True,
        #          'weight': 100,
        #          'note': 'this is a note'}
        #
        # self.loader.add_position(pdict)
        # with self.loader.db.session_ctx():
        #     obj = self.loader.db.get_irradiation_position('NM-1000', 'A', 1)
        #     self.assertTupleEqual((obj.labnumber.identifier, obj.position, obj.level.name, obj.level.irradiation.name),
        #                           (1000, 1, 'A', 'NM-1000'))
        #
class XLSIrradiationLoaderParseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = XLSIrradiationLoader()
        p = os.path.join(get_data_dir(), 'irradiation_import.xls')
        cls.input_path = p

    def tearDown(self):
        ip = os.path.join(get_data_dir(), 'template.xls')
        if os.path.isfile(ip):
            os.remove(ip)

    def setUp(self):
        self.loader.open(self.input_path)

    def test_make_template(self):
        ip = os.path.join(get_data_dir(), 'template.xls')
        self.loader.make_template(ip)
        self.assertTrue(os.path.isfile(ip))

    def test_irradiation1(self):
        p = get_data_dir()
        p = os.path.join(p, DBNAME)

        self.assertTrue(os.path.isfile(p))

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
        self.assertListEqual(self.loader.added_chronologies,
                             [('NM-1000', '2012-12-12 01:01:00', '2012-12-12 02:01:00', 1),
                              ('NM-1000', '2012-12-12 04:01:00', '2012-12-12 05:01:00', 1),
                              ('NM-1001', '2012-01-12 01:01:00', '2012-01-12 02:01:00', 1),
                              ('NM-1001', '2012-01-12 04:01:00', '2012-01-12 05:01:00', 10)])

    def test_add_positions(self):
        self.loader.add_positions()

        self.assertEqual(self.loader.added_positions[:6], [('NM-1000', 'A', 1),
                                                           ('NM-1000', 'A', 2),
                                                           ('NM-1000', 'A', 3),
                                                           ('NM-1000', 'B', 1),
                                                           ('NM-1000', 'B', 2),
                                                           ('NM-1000', 'B', 3)])


if __name__ == '__main__':
    unittest.main()

