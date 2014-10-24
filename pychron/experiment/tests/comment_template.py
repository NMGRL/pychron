
__author__ = 'ross'

import unittest

from pychron.experiment.utilities.comment_template import CommentTemplater


class MockFactory(object):
    irrad_level = 'A'
    irrad_hole = '9'


class CommentTemplaterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj=MockFactory()

    def test_render1(self):
        self._test_render('irrad_level : irrad_hole', 'A:9')

    def test_render2(self):
        self._test_render('irrad_level : irrad_hole SCLF', 'A:9SCLF')

    def test_render3(self):
        self._test_render('irrad_level : irrad_hole <SPACE> SCLF', 'A:9 SCLF')

    def _test_render(self, label, expected):
        ct = CommentTemplater()
        ct.label=label
        r = ct.render(self.obj)
        self.assertEqual(expected, r)


if __name__ == '__main__':
    unittest.main()
