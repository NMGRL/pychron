from __future__ import absolute_import
import os

from datetime import datetime

from pychron.core.helpers.filetools import unique_date_path

__author__ = "ross"

import unittest


class BackupTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dt = datetime.now().strftime("%m-%d-%Y")
        cls.root = ""

    def test_unique_date_path(self):
        self._test("a")

    def test_unique_date_path_underscore(self):
        self._test("a_1")

    def test_unique_date_path_dash(self):
        self._test("a-1")

    def _test(self, base):
        # make existing backup file
        p = os.path.join(self.root, "{}_{}-001.txt".format(base, self.dt))
        with open(p, "w"):
            pass

        p2 = unique_date_path(self.root, base)
        self.assertEqual(os.path.basename(p2), "{}_{}-002.txt".format(base, self.dt))
        os.remove(p)


if __name__ == "__main__":
    unittest.main()
