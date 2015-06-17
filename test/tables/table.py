import os
import subprocess

__author__ = 'ross'

import unittest

from pychron.core.ui import set_toolkit

set_toolkit('qt4')

from test.database import isotope_manager_factory
from pychron.pipeline.editors.step_heat.step_heat_table_editor import StepHeatTableEditor

from logging import getLogger

logger = getLogger('table')


class TableWriterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isotope_man = isotope_manager_factory(name='pychrondata_minnabluff')
        cls.isotope_man.db.connect()
        man = cls.isotope_man
        db = man.db

        cls.sample_id = sid = 'AF-72'
        #cls.analysis_id = aid = string.ascii_uppercase.index('A')

        with db.session_ctx():
            ans, tc = db.get_sample_analyses([sid, ], ['Minna Bluff'])
            cls.analyses = man.make_analyses(ans)

            #an = man.make_analysis(ans[aid])

            #cls.analysis = an

            #p = '../data/autoupdate_AF_72_1'
            #cls.parser = AutoupdateParser()
            #cls.parser.parse(p)

    def setUp(self):
        pass

    def test_nruns(self):
        self.assertEqual(len(self.analyses), 10)

    def test_write(self):
        writer = StepHeatTableEditor()
        writer.set_items(self.analyses)

        p = '/Users/ross/Sandbox/step_heat.pdf'
        writer.save_file(p, title='Table 1. Ar/Ar Step heat data.')
        self._view_file(p)

    def _view_file(self, p, application='Preview'):
        app_path = '/Applications/{}.app'.format(application)
        if not os.path.exists(app_path):
            app_path = '/Applications/Preview.app'

        subprocess.call(['open', '-a', app_path, p])
