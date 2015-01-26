import os
from pychron.core.test_helpers import get_data_dir, isotope_db_factory
from pychron.entry.loaders.xls_sample_loader import XLSSampleLoader

__author__ = 'ross'

import unittest
def fget_data_dir():
    op = 'pychron/entry/tests/data'
    return get_data_dir(op)
    # if not os.path.isdir(op):
    #     op = os.path.join('.', 'data')
    # return op


DBNAME ='sample_load.db'
def db_factory():
    path = os.path.join(fget_data_dir(), DBNAME)
    db = isotope_db_factory(path)
    # from pychron.database.adapters.isotope_adapter import IsotopeAdapter
    from pychron.database.orms.isotope.util import Base
    #
    # db = IsotopeAdapter()
    # db.verbose_retrieve_query = True
    # db.trait_set(kind='sqlite', path=os.path.join(get_data_dir(), DBNAME))
    # db.connect()
    #
    if os.path.isfile(db.path):
        os.remove(db.path)

    metadata = Base.metadata
    db.create_all(metadata)
    with db.session_ctx() as sess:
        metadata.create_all(sess.bind)

    return db


class SampleLoaderTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loader = XLSSampleLoader()
        cls.db = db_factory()

    def test_load_samples1(self):
        path = os.path.join(fget_data_dir(), 'sample_import.xls')
        self.loader.do_loading(None, self.db, path, dry=False, use_progress=False, quiet=True)

        db=self.db
        with db.session_ctx():
            dbsam = db.get_sample('foo-001')
            self.assertEqual(dbsam.name, 'foo-001')
            self.assertEqual(dbsam.project.name, 'bar')
            self.assertEqual(dbsam.material.name, 'bat')

    def test_load_samples2(self):
        path = os.path.join(fget_data_dir(), 'sample_import.xls')
        self.loader.do_loading(None, self.db, path, dry=False, use_progress=False, quiet=True)

        db=self.db
        with db.session_ctx():
            dbsam = db.get_sample('moo-002')
            self.assertEqual(dbsam.name, 'moo-002')
            self.assertEqual(dbsam.project.name, 'moobar')
            self.assertEqual(dbsam.material.name, 'bat')


if __name__ == '__main__':
    unittest.main()
