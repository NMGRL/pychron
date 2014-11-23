import time

from pychron.core.ui import set_qt

set_qt()

from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript

__author__ = 'ross'

import unittest


class ExtractionTestCase(unittest.TestCase):
    def setUp(self):
        self.s = ExtractionPyScript()
        self.s.root = '.'
        self.s.name = 'co2_v2.py'
        self.s.bootstrap()
        self.s.setup_context(analysis_type='blank',
                             cleanup=1, extract_value=1, duration=1)

    def test_something(self):
        ret = self.s.execute()
        self.assertEqual(ret, True)


class DummyDevice(object):
    _cnt = 0

    def get_value(self):
        self._cnt += 1
        return self._cnt


class DummyApplication(object):
    _dev = DummyDevice()

    def get_service_by_name(self, p, name):
        return self._dev


class DummyManager(object):
    application = DummyApplication()

    def set_extract_state(self):
        pass

    def info(self):
        pass


class WaitForTestCase(unittest.TestCase):
    def setUp(self):
        self.s = ExtractionPyScript(manager=DummyManager())
        # self.s.root = '.'
        # self.s.name = 'waitfor_test.py'
        # self.s.bootstrap()
        self.s.setup_context(analysis_type='blank',
                             cleanup=1, extract_value=1, duration=1)

    def test_waitfor_dev(self):
        self.s.text = '''
def main():
    waitfor(('dummy', 'get_value', 'x>2'))
'''
        ret = self.s.execute()
        self.assertEqual(ret, True)

    def test_waitfor_timing(self):
        self.s.text = '''
def main():
    waitfor(('dummy', 'get_value', 'x>2'))
'''
        st = time.time()
        self.s.execute()
        et = time.time() - st
        self.assertGreaterEqual(2, et)

    def test_waitfor_timeout(self):
        self.s.text = '''
def main():
    waitfor(('dummy', 'get_value', 'x>10'), timeout=3)
'''
        ret = self.s.execute()
        self.assertEqual(ret, False)

    def test_waitfor_func(self):
        self.s.text = '''
def func():
    def f(ti, c):
        return c>2
    return f

def main():
    waitfor(func())
'''
        ret = self.s.execute()
        self.assertEqual(ret, True)


if __name__ == '__main__':
    unittest.main()
