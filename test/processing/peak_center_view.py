from pychron.core.ui import set_toolkit
set_toolkit('qt4')

from pychron.processing.analyses.view.peak_center_view import PeakCenterView
import unittest

from test.database import isotope_manager_factory

class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isotope_man = isotope_manager_factory(name='pychrondata_dev')
        cls.isotope_man.db.connect()
        man = cls.isotope_man
        db = man.db
        with db.session_ctx():
            ans, tc = db.get_sample_analyses(['MB06-674', ], ['Minna Bluff'])

            an = man.make_analysis(ans[4])
            cls._id=ans[4].id
            cls.analysis_no_pc = an
            # print ans[4].id
    def test_load_peakcenter(self):
        pc=PeakCenterView()
        ret=pc.load(self.analysis_no_pc)
        self.assertTrue(ret)


if __name__ == '__main__':
    unittest.main()
