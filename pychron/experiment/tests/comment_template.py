
__author__ = 'ross'

import unittest

from pychron.experiment.automated_run.comment_template import CommentTemplater


class MockFactory(object):
    irrad_level = 'A'
    irrad_hole = '9'


class CommentTemplaterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj=MockFactory()

    def test_render(self):
        ct = CommentTemplater()
        ct.label='irrad_level : irrad_hole'
        r = ct.render(self.obj)
        self.assertEqual('A:9', r)


if __name__ == '__main__':
    unittest.main()
