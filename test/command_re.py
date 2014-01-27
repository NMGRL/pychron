import re

__author__ = 'ross'

import unittest

name_re=re.compile(r'''name\s*=\s*["']+\w+["']''')
desc_re=re.compile(r'''description\s*=\s*["']+[\w\s]+["']''')
attr_re=re.compile(r'''["']+[\w\s]+["']''')
vd={'A':'Foo Bar'}

class ValveCommand(object):
    valve=None
    def load_str(self, txt):
        m=name_re.match(txt)
        if m:
            a=self._extract_attr(m)
            if a:
                self.valve=a
                return

        m=desc_re.match(txt)
        if m:
            a=self._extract_attr(m)
            v=next((k for k, v in vd.iteritems() if v==a), None)
            if v:
                self.valve=v
                return

        if attr_re.match(txt):
            self.valve=txt[1:-1]

    def _extract_attr(self, m):
        name = m.group(0)
        a = attr_re.findall(name)[0]
        if a:
            return a[1:-1]



class ValveCase(unittest.TestCase):


    def setUp(self):
        self.cmd=ValveCommand()

    def testName(self):
        t='name="A"'
        self.cmd.load_str(t)
        self.assertEqual(self.cmd.valve, 'A')

    def testName2(self):
        t="name='A'"
        self.cmd.load_str(t)
        self.assertEqual(self.cmd.valve, 'A')

    def testNone(self):
        self.cmd.load_str("'A'")
        self.assertEqual(self.cmd.valve, 'A')

    def testDescription(self):
        t = "description='Foo Bar'"
        self.cmd.load_str(t)
        self.assertEqual(self.cmd.valve, 'A')

    def testBoth(self):
        t = "name='A',description='Foo'"
        self.cmd.load_str(t)
        self.assertEqual(self.cmd.valve, 'A')

    def testSwitchedBoth(self):
        t = "description='Foo Bar',name='A'"
        self.cmd.load_str(t)
        self.assertEqual(self.cmd.valve, 'A')


if __name__ == '__main__':
    unittest.main()
