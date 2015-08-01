import os
import sys
import shutil
import copy
from traits.has_traits import HasTraits

from pychron.core.test_helpers import isotope_db_factory, get_data_dir as mget_data_dir, massspec_db_factory
from pychron.experiment.utilities.identifier import make_runid
from pychron.processing.analysis_modifier import AnalysisModifier


__author__ = 'ross'

import unittest

if sys.platform == 'darwin':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('amod')


def get_data_dir():
    op = 'pychron/processing/tests/data'
    return mget_data_dir(op)


def pychron_source_factory():
    src = os.path.join(get_data_dir(), 'opychrondata.db')
    dest = os.path.join(get_data_dir(), 'pychrondata.db')

    # duplicate the original database
    shutil.copyfile(src, dest)

    db = isotope_db_factory(dest, remove=False)
    return db


def massspec_source_factory():
    src = os.path.join(get_data_dir(), 'omassspecdata.db')
    dest = os.path.join(get_data_dir(), 'massspecdata.db')

    # duplicate the original database
    shutil.copyfile(src, dest)

    db = massspec_db_factory(dest, remove=False)
    return db


class MAnalysis(object):
    identifier = labnumber = '1000'

    def __init__(self, dbrecord):
        self.identifier = dbrecord.labnumber.identifier
        self.labnumber = self.identifier
        self.aliquot = dbrecord.aliquot
        self.step = dbrecord.step
        self.uuid = dbrecord.uuid
        self.increment = dbrecord.increment

    @property
    def record_id(self):
        return make_runid(self.identifier, self.aliquot, self.step)


class AnalysisModifierTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = os.path.join(get_data_dir(), 'opychrondata.db')
        db = isotope_db_factory(src, remove=False)
        with db.session_ctx():
            ans = db.get_analyses()
            cls.analyses = [MAnalysis(ai) for ai in ans]
        cls.new_identifier = '2000'

    def setUp(self):
        maindb = pychron_source_factory()
        sdb = massspec_source_factory()

        self.modifier = AnalysisModifier(main_db=maindb,
                                         secondary_db=sdb)

    def test_modifier_pychrondb(self):
        self.modifier.use_main = True
        self.modifier.use_secondary = False

        an = self.analyses[0]
        can = copy.copy(an)
        can.identifier = self.new_identifier

        self.modifier.modify_analyses([an], [can])

        db = self.modifier.main_db
        with db.session_ctx():
            new_an = db.get_analysis_uuid(an.uuid)
            self.assertEqual(new_an.labnumber.identifier, self.new_identifier)

    def test_modifier_secondarydb(self):
        self.modifier.use_main = False
        self.modifier.use_secondary = True

        an = self.analyses[0]
        can = copy.copy(an)
        can.identifier = self.new_identifier
        self.modifier.modify_analyses([an], [can])

        db = self.modifier.secondary_db
        with db.session_ctx():
            old_an = db.get_analysis(an.labnumber, an.aliquot, an.step)
            self.assertIsNone(old_an)

            new_an = db.get_analysis(self.new_identifier, '{:02d}'.format(an.aliquot), an.step)
            self.assertEqual(new_an.RID, make_runid(self.new_identifier, an.aliquot, an.step))
            self.assertEqual(new_an.sample.Sample, 'Bar')


def generate_opychrondb():
    src = os.path.join(get_data_dir(), 'opychrondata.db')
    db = isotope_db_factory(src)
    with db.session_ctx():
        db.add_labnumber('1000')
        db.add_labnumber('2000')
        db.flush()

        for i in range(3):
            db.add_analysis('1000', aliquot=i + 1)


def generate_omassspecdb():
    src = os.path.join(get_data_dir(), 'omassspecdata.db')
    db = massspec_db_factory(src)
    with db.session_ctx():
        s = db.add_sample('Foo')
        db.flush()
        db.add_irradiation_position('1000', 'NM-100A', 1, sample=s.SampleID)

        s = db.add_sample('Bar')
        db.flush()
        db.add_irradiation_position('2000', 'NM-100A', 2, sample=s.SampleID)

        db.flush()

        for i in range(3):
            rid = make_runid('1000', i + 1)
            db.add_analysis(rid, i + 1, '', '1000', 1)


if __name__ == '__main__':
    unittest.main()

    # generate_opychrondb()
    # generate_omassspecdb()

