from pychron.ui import set_toolkit

set_toolkit('qt4')

from pychron.paths import paths

paths.build('_unittest')
#build_directories(paths)

from pychron.helpers.logger_setup import logging_setup

logging_setup('packager')

from test.database import isotope_manager_factory
from pychron.processing.vcs_data.packager import Packager



import unittest


class ArArAgeCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isotope_man = isotope_manager_factory(name='pychrondata_minnabluff')
        cls.isotope_man.db.connect()
        man = cls.isotope_man
        db = man.db
        with db.session_ctx():
            ans, tc = db.get_sample_analyses(['AF-72', ], ['Minna Bluff'])
            cls.analyses=man.make_analyses(ans)
            cls.analysis = ans[0]

        cls.pkg=Packager()

    def test_packaging(self):
        pkg=self.pkg
        pkg.package(self.analyses)

if __name__ == '__main__':
    unittest.main()
