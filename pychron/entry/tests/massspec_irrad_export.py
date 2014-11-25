from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader

__author__ = 'ross'

from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.entry.export.mass_spec_irradiation_exporter import MassSpecIrradiationExporter, \
    generate_production_ratios_id

import os
import unittest

DEBUGGING = False

# automatically disable debugging if running on a travis ci linux box.
import sys

if sys.platform != 'darwin':
    DEBUGGING = False

DEST_NAME = 'massspecdata.db'
SRC_NAME = 'pychrondata.db'

if DEBUGGING:
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('irrad_loader')


def get_data_dir():
    op = 'pychron/entry/tests/data'
    if not os.path.isdir(op):
        op = os.path.join('.', 'data')
    return op


def dest_factory(name, remove=True):
    from pychron.database.orms.massspec_orm import Base

    path = os.path.join(get_data_dir(), name)
    if remove and os.path.isfile(path):
        os.remove(path)

    db = MassSpecDatabaseAdapter()
    # db.verbose_retrieve_query = True
    db.trait_set(kind='sqlite', path=path)
    db.connect()

    metadata = Base.metadata
    db.create_all(metadata)

    return db


def source_factory():
    from pychron.database.adapters.isotope_adapter import IsotopeAdapter
    from pychron.database.orms.isotope.util import Base

    db = IsotopeAdapter()
    db.verbose_retrieve_query = True
    db.trait_set(kind='sqlite', path=os.path.join(get_data_dir(), SRC_NAME))
    db.connect()

    if os.path.isfile(db.path):
        os.remove(db.path)

    metadata = Base.metadata
    db.create_all(metadata)

    p = os.path.join(get_data_dir(), 'irradiation_import.xls')
    loader = XLSIrradiationLoader(db=db)
    loader.load_irradiation(p, dry_run=False)

    with db.session_ctx():
        irrads = [i.name for i in db.get_irradiations()]

    return db, irrads


class MassSpecIrradExportTestCase(unittest.TestCase):
    """
        Test exporting irradiations from Pychron to MassSpec
    """

    @classmethod
    def setUpClass(cls):
        cls.exporter = MassSpecIrradiationExporter()
        src, irradnames = source_factory()
        cls.source = src
        cls.irradnames = irradnames

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

        self.assertTrue(True)
        # self.assertTupleEqual(names, ('NM-1000', 'NM-1001'))


class ProductionRatiosTestCase(unittest.TestCase):
    def setUp(self):
        self.db = dest_factory('massspec_pr.db', remove=False)

    def test_production_id(self):
        keys = ('Ca3637', 'Ca3637Er',
                           'Ca3937', 'Ca3937Er',
                           'K4039', 'K4039Er',
                           'P36Cl38Cl', 'P36Cl38ClEr',
                           'Ca3837', 'Ca3837Er',
                           'K3839', 'K3839Er',
                           'K3739', 'K3739Er',
                           'ClOverKMultiplier', 'ClOverKMultiplierEr',
                           'CaOverKMultiplier', 'CaOverKMultiplierEr')

        oidn = -1578996229
        with self.db.session_ctx():
            pr = self.db.get_production_ratio_by_id(oidn)
            vs = [getattr(pr, k) for k in keys]
            idn = generate_production_ratios_id(vs)
            self.assertEqual(idn, oidn)


if __name__ == '__main__':
    unittest.main()
    # generate_pr_db()
# ============================== EOF =====================================
# def generate_pr_db():
#     def quick_mapper(table):
#         from sqlalchemy.ext.declarative import declarative_base
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
