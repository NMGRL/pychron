__author__ = 'ross'

import os
import unittest

from pychron.core.ui import set_qt


set_qt()

from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader


TEST_PARSE_XLS = False

DBNAME = 'loader.db'


def get_data_dir():
    op = 'pychron/entry/tests/data'
    if not os.path.isdir(op):
        op = os.path.join('.', 'data')
    return op


def db_factory():
    from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
    from pychron.database.orms.massspec_orm import Base


    db = MassSpecDatabaseAdapter()
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
        p = 'pychron/entry/tests/data/irradiation_import.xls'
        if not os.path.isfile(p):
            p = './data/irradiation_import.xls'
        cls.input_path = p

    def setUp(self):
        self.loader.open(self.input_path)
        # rebuild the local db
        self.loader.db = db_factory()

    # def test_load_irradiation(self):
    # ret = self.loader.load_irradiation(self.input_path)
    #     self.assertTrue(ret)

    def test_add_irradiation_dry(self):
        self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1, dry=True)
        obj = self.loader.db.get_irradiation_level('NM-1000', 'A')
        self.assertIsNone(obj)

    def test_add_irradiation(self):
        self.loader.add_irradiation_level('NM-1000', 'A', '8-Hole', 1)
        with self.loader.db.session_ctx():
            obj = self.loader.db.get_irradiation_level('NM-1000', 'A')
            self.assertEqual(obj.IrradBaseID, 'NM-1000')


class XLSIrradiationLoaderParseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = XLSIrradiationLoader()
        p = 'pychron/entry/tests/data/irradiation_import.xls'
        if not os.path.isfile(p):
            p = './data/irradiation_import.xls'
        cls.input_path = p

    def setUp(self):
        self.loader.open(self.input_path)

    def test_make_template(self):
        op = get_data_dir()
        # op = './data'

        self.loader.make_template(os.path.join(op, 'template.xls'))
        ip = 'pychron/entry/tests/template.xls'
        if not os.path.isfile(ip):
            ip = os.path.join('.', 'data', 'template.xls')

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


if __name__ == '__main__':
    unittest.main()

