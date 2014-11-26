import os
import shutil

from pychron.core.test_helpers import isotope_db_factory, get_data_dir as mget_data_dir
from pychron.experiment.utilities.identifier import make_runid
from pychron.processing.analysis_modifier import AnalysisModifier


__author__ = 'ross'

import unittest


def get_data_dir():
    op = 'pychron/processing/tests/data'
    return mget_data_dir(op)


def source_factory():
    src = os.path.join(get_data_dir(), 'opychrondata.db')
    dest = os.path.join(get_data_dir(), 'pychrondata.db')

    # duplicate the original database
    shutil.copyfile(src, dest)

    db = isotope_db_factory(dest, remove=False)
    return db


class MAnalysis(object):
    identifier = labnumber = '1000'

    def __init__(self, dbrecord):
        self.identifier = dbrecord.labnumber.identifier
        self.labnumber = self.identifier
        self.aliquot = dbrecord.aliquot
        self.step = dbrecord.step
        self.uuid = dbrecord.uuid

        self.record_id = make_runid(self.identifier, self.aliquot, self.step)


class AnalysisModifierTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = os.path.join(get_data_dir(), 'opychrondata.db')
        db = isotope_db_factory(src, remove=False)
        with db.session_ctx():
            ans = db.get_analyses()
            cls.analyses = [MAnalysis(ai) for ai in ans]

    def setUp(self):
        maindb = source_factory()
        self.modifier = AnalysisModifier(main_db=maindb)

    def test_modifier_pychrondb(self):
        self.modifier.use_main = True
        self.modifier.use_secondary = False

        an = self.analyses[0]
        self.modifier.modify_analyses([an], '2000')

        db = self.modifier.main_db
        with db.session_ctx():
            new_an = db.get_analysis_uuid(an.uuid)
            self.assertEqual(new_an.labnumber.identifier, '2000')


def generate_odb():
    src = os.path.join(get_data_dir(), 'opychrondata.db')
    db = isotope_db_factory(src)
    with db.session_ctx():
        db.add_labnumber('1000')
        db.add_labnumber('2000')
        db.flush()

        for i in range(3):
            db.add_analysis('1000', aliquot=i + 1)


if __name__ == '__main__':
    unittest.main()
    # generate_odb()