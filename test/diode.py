from pychron.globals import globalv
from pychron.ui import set_toolkit

set_toolkit('qt4')

from pychron.paths import paths

paths.build('_unittest')
#build_directories(paths)

from pychron.helpers.logger_setup import logging_setup
from pychron.lasers.laser_managers.fusions_diode_manager import FusionsDiodeManager

logging_setup('arar')
import unittest

globalv.ignore_connection_warnings=True

class Diode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manager = FusionsDiodeManager()
        cls.manager.temperature_controller.bootstrap()

    def test_pid_bins_first(self):
        temp=300
        pd=self.manager._get_pid_bin(temp)
        self.assertEqual(pd, [0.0,0.0,0.0])

    def test_pid_bins(self):
        temp = 600
        pd = self.manager._get_pid_bin(temp)
        self.assertEqual(pd, [20.0, 0.2, 22.0])

    def test_pid_bins_fail(self):
        temp = 2000
        pd = self.manager._get_pid_bin(temp)
        self.assertEqual(pd, [200.0, 20.0, 2.0])
