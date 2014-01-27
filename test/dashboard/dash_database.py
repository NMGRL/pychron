from datetime import datetime
import unittest
from pychron.paths import paths, build_directories
from pychron.core.ui import set_toolkit
set_toolkit('qt4')

paths.build('_unittest')
build_directories(paths)

from pychron.dashboard.db_manager import DashboardDBManager
from pychron.dashboard.server import DashboardServer

class DashboardDatabaseCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        man=DashboardDBManager(connect=False)
        man.db.kind = 'mysql'
        man.db.name = 'isotopedb_dev'
        man.db.password = 'Argon'
        man.db.username = 'root'
        man.db.host = 'localhost'
        man.db.connect()
        cls.man=man

        cls.server=DashboardServer()
        cls.server.db_manager=man
        cls.server._load_devices()

    def test_stoptimetable(self):

        self.man.stop()
        ts = datetime.now()

        db = self.man.db
        with db.session_ctx():
            tt = db.get_last_time_table()
            self.assertEqual(ts.date(), tt.end.date())

    def test_starttimetable(self):
        self.man.start()

        ts=datetime.now()

        db=self.man.db
        with db.session_ctx():
            tt=db.get_last_time_table()
            self.assertEqual(ts.date(), tt.start.date())

    def test_push(self):

        dev=self.server.devices[0]
        self.man.publish_device(dev)
        self.man.publish_device(dev)
        self.man.publish_device(dev)
        self.man.publish_device(dev)
        self.man.publish_device(dev)
        # self.assertEqual(True, False)

    # def test_unpack(self):
    #     db = self.man.db
    #     with db.session_ctx():
    #         tt = db.get_last_time_table()
    #         dev=tt.devices[0]
    #
    #         self.server.devices.new_scan_blob()
    #         self.assertEqual(dev)

if __name__ == '__main__':
    unittest.main()
