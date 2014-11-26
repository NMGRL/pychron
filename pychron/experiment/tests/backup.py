from datetime import datetime
import os

from pychron.core.helpers.filetools import unique_date_path
from pychron.core.test_helpers import get_data_dir as mget_data_dir


__author__ = 'ross'

import unittest


def get_data_dir():
    op = 'pychron/experiment/tests/data'
    return mget_data_dir(op)


class BackupTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dt = datetime.now().strftime('%m-%d-%Y')
        cls.root = get_data_dir()

    def test_unique_date_path(self):
        self._test('a')

    def test_unique_date_path_underscore(self):
        self._test('a_1')

    def test_unique_date_path_dash(self):
        self._test('a-1')

    def _test(self, base):
        # make existing backup file
        p = os.path.join(self.root, '{}_{}-001.txt'.format(base, self.dt))
        with open(p, 'w'):
            pass

        p = unique_date_path(self.root, base)
        self.assertEqual(os.path.basename(p), '{}_{}-002.txt'.format(base, self.dt))


if __name__ == '__main__':
    unittest.main()
