import unittest

from pychron.git_archive.diff_util import extract_line_numbers  # extract_line_changes, extract_line_changes2


class DiffTestCase(unittest.TestCase):
    def _test_modify(self, a, b, els, ers):
        ls, rs = extract_line_numbers(a, b)
        self.assertListEqual(ls, els)
        self.assertListEqual(rs, ers)

    def test_modify_add(self):
        a = '''a=1
b=1'''
        b = '''a=1
b=1
c=2'''
        self._test_modify(a, b, [], [2])

    def test_modify1(self):
        a = '''a=1
b=1'''
        b = '''a=2
b=1'''
        self._test_modify(a, b, [0], [0])

    def test_modify2(self):
        a = '''a=1
b=1'''
        b = '''a=1
b=2'''
        self._test_modify(a, b, [1], [1])

    def test_modify3(self):
        a = '''a=2
b=1'''
        b = '''a=1
b=1'''
        self._test_modify(a, b, [0], [0])

    def test_diff_sub(self):
        a = '''a=1
b=1'''
        b = '''a=1
b=1
c=1'''
        self._test_modify(b, a, [2], [])

    def test_modify_sameline_add(self):
        a = '''a=1
b=1'''
        b = '''a=12
b=1'''
        self._test_modify(a, b, [0], [0])

    def test_modify_sameline_sub(self):
        a = '''a=1
b=1'''
        b = '''a=12
b=1'''
        self._test_modify(b, a, [0], [0])

    def test_add_line(self):
        a = '''a=1
b=1'''
        b = '''a=1
c=12
b=1'''
        self._test_modify(a, b, [], [1])


if __name__ == '__main__':
    unittest.main()
