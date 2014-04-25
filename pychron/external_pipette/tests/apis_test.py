__author__ = 'ross'

import unittest

from pychron.hardware.apis_controller import ApisController


class ApisTestCase(unittest.TestCase):
    def setUp(self):
        self.c = ApisController()

    def test_list_blanks(self):
        cmd = self.c.make_command('list_blanks')
        self.assertEqual(cmd, '100')

    def test_list_airs(self):
        cmd = self.c.make_command('list_airs')
        self.assertEqual(cmd, '101')

    def test_last_runid(self):
        cmd = self.c.make_command('last_runid')
        self.assertEqual(cmd, '102')

    def test_pipette_recod(self):
        cmd = self.c.make_command('pipette_record')
        self.assertEqual(cmd, '103')

    def test_status(self):
        cmd = self.c.make_command('status')
        self.assertEqual(cmd, '104')

    def test_load_blank(self):
        cmd = self.c.make_command('load_blank')
        self.assertEqual(cmd, '105')

    def test_load_air(self):
        cmd = self.c.make_command('load_air')
        self.assertEqual(cmd, '106')

    def test_cancel(self):
        cmd = self.c.make_command('cancel')
        self.assertEqual(cmd, '107')

    def test_external_pumping(self):
        cmd = self.c.make_command('set_external_pumping')
        self.assertEqual(cmd, '108')


if __name__ == '__main__':
    unittest.main()
