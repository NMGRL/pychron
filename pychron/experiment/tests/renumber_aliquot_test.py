from pychron.experiment.utilities.aliquot_numbering import renumber_aliquots

__author__ = 'ross'

import unittest


class MockRun(object):
    def __init__(self, l, uda, pos):
        self.labnumber = l
        self.user_defined_aliquot = uda
        self.position = pos


class RenumberAliquotTestCase(unittest.TestCase):

    def test_renumber(self):
        runs = [MockRun('12345', 2, 2),
                MockRun('12345', 2, 2),
                MockRun('12345', 2, 2),
                MockRun('bu-01-01', 0, 0),
                MockRun('12345', 1, 1),
                MockRun('12345', 1, 1),
                MockRun('12345', 1, 1),
                MockRun('12345', 3, 3),
                MockRun('12345', 3, 3),
                MockRun('12345', 3, 3),
                ]

        renumber_aliquots(runs)

        r=runs[0]
        self.assertTupleEqual((r.user_defined_aliquot, r.position),
                              (1,2))

        r=runs[1]
        self.assertTupleEqual((r.user_defined_aliquot, r.position),
                              (1,2))

        r=runs[5]
        self.assertTupleEqual((r.user_defined_aliquot, r.position),
                              (2,1))

        r=runs[7]
        self.assertTupleEqual((r.user_defined_aliquot, r.position),
                              (3,3))

if __name__ == '__main__':
    unittest.main()
