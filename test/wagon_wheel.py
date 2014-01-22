__author__ = 'ross'

import unittest

def wagon_wheel(n, o):
    if not hasattr(o,'__iter__'):
        o=(o,)

    def gen():
        pv=0
        yield 0
        for i in range(1, n+1, 1):
            for oi in o:
                vi=pv+oi
                if vi>n:
                    vi=vi-n

                if vi==n:
                    vi=0

                yield vi
                pv=vi

    return gen()

class WagonwheelCase(unittest.TestCase):
    def test_eight(self):

        pos=list(wagon_wheel(8, 5))

        self.assertEqual(pos, [0,3,6,1,4,7,2,5,0])

    def test_six(self):
        pos = list(wagon_wheel(6, (3, 2)))
        self.assertEqual(pos, [0, 3, 5, 2, 4, 1, 3, 0, 2, 5, 1, 4, 0])

    def test_ten(self):
        pos = list(wagon_wheel(10, (5, 4, 3)))
        print pos
        self.assertEqual(True, False)

if __name__ == '__main__':
    unittest.main()
