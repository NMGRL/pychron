__author__ = 'ross'
import os
import unittest

from pychron.core.test_helpers import isotope_db_factory, massspec_db_factory, get_data_dir as mget_data_dir
from pychron.entry.export.mass_spec_irradiation_exporter import MassSpecIrradiationExporter, \
    generate_production_ratios_id
from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader
from pychron.mass_spec.database.massspec_database_adapter import PR_KEYS

DEBUGGING = True
LOGGING = True
# automatically disable debugging if running on a travis ci linux box.
import sys

if sys.platform != 'darwin':
    DEBUGGING = False
    LOGGING = False

DEST_NAME = 'massspecdata.db'
SRC_NAME = 'pychrondata.db'

if LOGGING:
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('irrad_loader', use_archiver=False, use_file=False)


def get_data_dir():
    return mget_data_dir('pychron/entry/tests/data')


def dest_factory(name, remove=True):
    path = os.path.join(get_data_dir(), name)
    db = massspec_db_factory(path, remove)
    return db


def source_factory():
    db = isotope_db_factory(os.path.join(get_data_dir(), SRC_NAME))
    p = os.path.join(get_data_dir(), 'irradiation_import.xls')

    # add a production ratio
    with db.session_ctx():
        db.add_irradiation_production(name='Triga PR', K4039=10)

    loader = XLSIrradiationLoader(db=db)
    loader.open(p)
    loader.load_irradiation(p, dry_run=False)
    db.verbose = False
    with db.session_ctx():
        dbirrads = db.get_irradiations(order_func='asc')
        irrads = [i.name for i in dbirrads]

        levels = {}
        for di in dbirrads:
            levels[di.name] = tuple([li.name for li in di.levels])

    return db, irrads, levels


class MassSpecIrradExportTestCase(unittest.TestCase):
    """
        Test exporting irradiations from Pychron to MassSpec
    """

    @classmethod
    def setUpClass(cls):
        cls.exporter = MassSpecIrradiationExporter()
        src, irradnames, levels = source_factory()
        cls.source = src
        cls.irradnames = irradnames
        cls.levels = levels

    def setUp(self):
        dest = dest_factory(DEST_NAME)

        self.exporter.source = self.source
        self.exporter.destination = dest

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_export_chronology(self):
        name = self.irradnames[0]
        self.exporter.export_chronology(name)

        dest = self.exporter.destination
        with dest.session_ctx():
            chrons = dest.get_chronology_by_irradname(name)
            self.assertEqual(len(chrons), 2)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_export_irrad(self):
        self.exporter.do_export(self.irradnames)

        dest = self.exporter.destination
        with dest.session_ctx():
            names = tuple(dest.get_irradiation_names())

        self.assertTupleEqual(names, ('NM-1000', 'NM-1001'))

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_levels1(self):
        self.exporter.do_export(self.irradnames)

        name = self.irradnames[0]
        dest = self.exporter.destination
        with dest.session_ctx():
            names = tuple(dest.get_irradiation_level_names(name))

        self.assertTupleEqual(names, self.levels[name])

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_levels2(self):
        self.exporter.do_export(self.irradnames)

        name = self.irradnames[1]
        dest = self.exporter.destination
        with dest.session_ctx():
            names = tuple(dest.get_irradiation_level_names(name))

        self.assertTupleEqual(names, self.levels[name])

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_positions(self):
        self.exporter.do_export(self.irradnames)
        dest = self.exporter.destination
        with dest.session_ctx():
            iname = self.irradnames[0]
            pos = dest.get_irradiation_positions(iname, self.levels[iname][0])
            self.assertEqual(len(pos), 3)


class ProductionRatiosTestCase(unittest.TestCase):
    def setUp(self):
        self.db = dest_factory('massspec_pr.db', remove=False)

    def test_production_id(self):

        oidn = -1578996229
        with self.db.session_ctx():
            pr = self.db.get_production_ratio_by_id(oidn)
            vs = [getattr(pr, k) for k in PR_KEYS]
            idn = generate_production_ratios_id(vs)
            self.assertEqual(idn, oidn)


if __name__ == '__main__':
    unittest.main()
    # generate_pr_db()
# ============================== EOF =====================================
# def generate_pr_db():
# def quick_mapper(table):
# from sqlalchemy.ext.declarative import declarative_base
#
#         Base = declarative_base()
#
#         class GenericMapper(Base):
#             __table__ = table
#
#         return GenericMapper
#
#     def copy_record(src, dest, pid):
#         from pychron.database.orms.massspec_orm import Base
#         from sqlalchemy import Table
#
#         meta = Base.metadata
#         with src.session_ctx() as sess:
#             meta.bind = sess.bind
#
#             table = Table('IrradiationProductionTable', meta, autoload=True)
#             nrec = quick_mapper(table)
#             columns = table.columns.keys()
#
#             q = sess.query(table)
#             q = q.filter(table.c.ProductionRatiosID == pid)
#             record = q.one()
#             data = dict([(str(column), getattr(record, column)) for column in columns])
#             with dest.session_ctx() as dsess:
#                 dsess.merge(nrec(**data))
#
#     dest = dest_factory('massspec_pr.db')
#     src = MassSpecDatabaseAdapter(host='localhost',
#                                   name='massspecdata_crow',
#                                   username='root', password='Argon')
#     src.connect()
#
#     copy_record(src, dest, -1578996229)
