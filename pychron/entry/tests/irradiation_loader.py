from pychron.core.test_helpers import get_data_dir as mget_data_dir, dvc_db_factory

__author__ = 'ross'

import os
import unittest

from pychron.core.ui import set_qt

set_qt()

from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader

TEST_PARSE_XLS = False
DEBUGGING = False

# automatically disable debugging if running on a travis ci linux box.
import sys

if sys.platform != 'darwin':
    DEBUGGING = False

DBNAME = 'loader.db'

if DEBUGGING:
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('irrad_loader')


def get_data_dir():
    op = 'pychron/entry/tests/data'
    return mget_data_dir(op)
    # if not os.path.isdir(op):
    #     op = os.path.join('.', 'data')
    # return op


def db_factory():
    path = os.path.join(get_data_dir(), DBNAME)
    db = dvc_db_factory(path)
    # from pychron.database.adapters.isotope_adapter import IsotopeAdapter
    # from pychron.database.orms.isotope.util import Base
    #
    # db = IsotopeAdapter()
    # db.verbose_retrieve_query = True
    # db.trait_set(kind='sqlite', path=os.path.join(get_data_dir(), DBNAME))
    # db.connect()
    #
    # if os.path.isfile(db.path):
    #     os.remove(db.path)
    #
    # metadata = Base.metadata
    # db.create_all(metadata)
    # with db.session_ctx() as sess:
    # metadata.create_all(sess.bind)

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

    # @unittest.skipIf(DEBUGGING, 'Debugging tests')
    # def test_add_irradiation_dry(self):
    #     self.loader.db.add_irradiation('NM-1000', dry=True)
    #     obj = self.loader.db.get_irradiation('NM-1000')
    #     self.assertIsNone(obj)

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_irradiation(self):
        self.loader.db.add_irradiation('NM-1000')
        with self.loader.db.session_ctx():
            obj = self.loader.db.get_irradiation('NM-1000')
            self.assertEqual(obj.name, 'NM-1000')

    # @unittest.skipIf(DEBUGGING, 'Debugging tests')
    # def test_add_level_dry(self):
    #     self.loader.add_irradiation('NM-1000')
    #     self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1, dry=True)
    #     obj = self.loader.db.get_irradiation_level('NM-1000', 'A')
    #     self.assertIsNone(obj)

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_level(self):
        self.loader.db.add_irradiation('NM-1000')
        self.loader.db.add_irradiation_level('A', 'NM-1000', '8-Hole', 'TRIGA', 1)

        with self.loader.db.session_ctx():
            obj = self.loader.db.get_irradiation_level('NM-1000', 'A')
            self.assertTupleEqual((obj.irradiation.name, obj.name),
                                  ('NM-1000', 'A'))

    def _default_pdict(self, **kw):
        pdict = {'irradiation': 'NM-1000',
                 'level': 'A',
                 'position': 1,
                 'material': 'sanidine',
                 'project': 'Test',
                 'sample': 'FC-2',
                 'is_monitor': True,
                 'weight': 100,
                 'identifier': None,
                 'note': 'this is a note'}
        pdict.update(**kw)
        return pdict

    # @unittest.skipIf(DEBUGGING, 'Debugging tests')
    # def test_add_position_dry(self):
    #     self.loader.add_irradiation('NM-1000')
    #     self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1, add_positions=False)
    #     pdict = self._default_pdict()
    #
    #     self.loader.add_position(pdict, dry=True)
    #
    #     obj = self.loader.db.get_irradiation_position('NM-1000', 'A', 1)
    #     self.assertIsNone(obj)

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_add_position(self):
        self.loader.db.add_irradiation('NM-1000')
        self.loader.db.add_irradiation_level('A', 'NM-1000', '8-Hole', 'TRIGA', 1)

        self.loader.db.add_irradiation_position('NM-1000', 'A', 1)
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
        self.assertTupleEqual((io, lo), (1000, 0))

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_generate_labnumber(self):
        # add a placeholder labnumber
        # self.loader.db.add_labnumber(1000, 'FC-2')

        # fool loader into thinking 1 irradiation and 1 level were added
        self.loader._added_irradiations = [0]
        self.loader._added_levels = [0]

        gen = self.loader.identifier_generator()

        self.assertEqual((gen.next(), gen.next()), (1000, 1001))

    @unittest.skipIf(DEBUGGING, 'Debugging tests')
    def test_generate_labnumber2(self):
        # add a placeholder labnumber
        self.loader.db.add_irradiation('NM-1000')
        self.loader.db.add_irradiation_level('A', 'NM-1000', '8-Hole', 'TRIGA', 1)
        self.loader.db.add_irradiation_position('NM-1000', 'A', 1, identifier='2500')

        # fool loader into thinking 1 irradiation and 1 level were added
        self.loader._added_irradiations = [0]
        self.loader._added_levels = [0]

        gen = self.loader.identifier_generator()

        self.assertEqual((gen.next(), gen.next()), (3500, 3501))

        # @unittest.skipIf(DEBUGGING, 'Debugging tests')
        # def test_generate_offsets2(self):
        #     # add a placeholder labnumber
        #     self.loader.db.add_labnumber(1000, 'FC-2')
        #
        #     # fool loader into thinking 2 irradiations and 8 level were added (4 to each irradiation)
        #     self.loader._added_irradiations = [0]
        #     self.loader._added_levels = [0, 0, 0, 0]
        #
        #     gen = self.loader.identifier_generator()
        #     self.assertEqual(tuple([gen.next() for i in range(4)]), (2030, 2031, 2032, 2033))
        #
        #     self.loader._added_irradiations = [0, 1]
        #     self.loader._added_levels = [1]
        #     gen = self.loader.identifier_generator()
        #     self.assertEqual(tuple([gen.next() for i in range(4)]), (3000, 3001, 3002, 3003))

        # @unittest.skipIf(DEBUGGING, 'Debugging tests')
        # def test_add_samples(self):
        #     self.loader.autogenerate_labnumber = True
        #     self.loader.add_irradiation('NM-1000')
        #     self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1, add_positions=False)
        #     gen = self.loader.identifier_generator()
        #     for i in range(3):
        #         pdict = self._default_pdict(identifier=gen.next())
        #         self.loader.add_position(pdict)
        #
        #     with self.loader.db.session_ctx():
        #         ps = self.loader.db.get_projects()
        #         self.assertEqual(len(ps), 1)
        #
        #         ms = self.loader.db.get_materials()
        #         self.assertEqual(len(ms), 1)
        #
        #         ss = self.loader.db.get_samples()
        #         self.assertEqual(len(ss), 1)


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

    def test_iteration3(self):
        p = os.path.join(get_data_dir(), 'iterate_irradiations.xls')
        self.loader.open(p)

        irrads = self.loader.iterate_irradiations()
        irrads = list(irrads)
        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[0]],
                             [('NM-1000', 'A'), ('NM-1000', 'B')])

    def test_iteration4(self):
        p = os.path.join(get_data_dir(), 'iterate_irradiations1.xls')
        self.loader.open(p)

        irrads = self.loader.iterate_irradiations()
        irrads = list(irrads)
        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[0]],
                             [('NM-1000', 'A'), ('', 'B'), ('', 'C')])

        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[1]],
                             [('NM-1001', 'A'), ('', 'B')])

    def test_iteration4(self):
        p = os.path.join(get_data_dir(), 'iterate_irradiations2.xls')
        self.loader.open(p)

        irrads = self.loader.iterate_irradiations()
        irrads = list(irrads)
        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[0]],
                             [('NM-1000', 'A'), ('', 'B'), ('NM-1000', 'C')])

        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[1]],
                             [('NM-1001', 'A'), ('', 'B')])

    def test_iteration4(self):
        p = os.path.join(get_data_dir(), 'iterate_irradiations3.xls')
        self.loader.open(p)

        irrads = self.loader.iterate_irradiations()
        irrads = list(irrads)
        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[0]],
                             [('NM-1000', 'A'), ('', 'B'), ('NM-1000', 'C')])

        self.assertListEqual([(i[0].value, i[1].value) for i in irrads[1]],
                             [('NM-1001', 'A'), ('NM-1001', 'B')])

    def test_add_irradiations(self):
        self.loader.add_irradiations()
        self.assertEqual(self.loader.added_irradiations, ['NM-1000', 'NM-1001'])

    def test_add_levels(self):
        self.loader.add_irradiations()
        self.assertEqual(self.loader.added_levels, [('NM-1001', 'A', 'Triga PR', '8-Hole'),
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

    def test_config_autogen(self):
        self.assertFalse(self.loader.autogenerate_labnumber)

    def test_config_ioffset(self):
        self.assertEqual(self.loader.base_irradiation_offset, 1000)

    def test_config_loffset(self):
        self.assertEqual(self.loader.base_level_offset, 10)

    def test_config_quiet(self):
        self.assertTrue(self.loader.quiet)


class SimilarTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = dvc_db_factory(os.path.join(get_data_dir(), 'similar.db'), remove=False, echo=True)

    def test_similar_pi_lower(self):
        with self.db.session_ctx():
            obj = self.db.get_similar_pi('ferguson')
            self.assertEqual(obj.name, 'Ferguson')

    def test_similar_pi_misspell(self):
        with self.db.session_ctx():
            obj = self.db.get_similar_pi('fergsuon')
            self.assertEqual(obj.name, 'Ferguson')

    def test_similar_material_lower(self):
        with self.db.session_ctx():
            obj = self.db.get_similar_material('sanidine')
            self.assertEqual(obj.name, 'Sanidine')

    def test_similar_materail_misspell(self):
        with self.db.session_ctx():
            obj = self.db.get_similar_material('sandine')
            self.assertEqual(obj.name, 'Sanidine')

if __name__ == '__main__':
    unittest.main()
