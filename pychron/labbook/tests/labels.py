from pychron.labbook.labeler import Labeler

__author__ = 'ross'

import unittest


class LabelTestCase(unittest.TestCase):
    def setUp(self):
        self.labeler = Labeler()

    def test_add_label(self):
        self.labeler.add_label('Label1', '000000FF')
        label = self.labeler.get_label('Label1')
        self.assertEqual(label.color, '000000FF')

    def test_delete_label(self):
        self.labeler.add_label('Label2', '00000055')
        label = self.labeler.get_label('Label2')
        self.assertEqual(label.color, '00000055')

        self.labeler.delete_label('Label2')
        label = self.labeler.get_label('Label2')
        self.assertIsNone(label)

    def test_add_label_to_path(self):
        self.labeler.add_label_to_path('a/b/c/foo.txt', 'Label1')
        dp = self.labeler.get_path('a/b/c/foo.txt')
        self.assertEqual(dp.labels_strings, ['Label1'])

    def test_add_label_to_path2(self):
        self.labeler.add_label('Label3', '00000044')
        self.labeler.add_label_to_path('a/b/c/foo.txt', 'Label3')
        dp = self.labeler.get_path('a/b/c/foo.txt')
        self.assertEqual(dp.labels_strings, ['Label1', 'Label3'])


if __name__ == '__main__':
    unittest.main()
