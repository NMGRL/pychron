from traits.has_traits import HasTraits

from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.experiment.utilities.identifier import is_special


__author__ = 'ross'

import unittest


class MockRun(HasTraits):
    def __init__(self, l, uda, pos):
        self.labnumber = l
        self.aliquot = uda
        # self.user_defined_aliquot = uda
        self.position = pos
        self.user_defined_aliquot = 0

    def is_step_heat(self):
        return bool(self.user_defined_aliquot) and not self.is_special()

    def is_special(self):
        return is_special(self.labnumber)

    def reset(self):
        self.clear_step()
        self.conflicts_checked = False

    def clear_step(self):
        self._step = -1


class ResetQueuesTestCase(unittest.TestCase):
    def setUp(self):
        self.queue= ExperimentQueue()
        eruns = [MockRun('12345',5, 1),
                 MockRun('12346',10,2)]
        self.queue.executed_runs=eruns

    def test_an(self):
        self.queue.reset()
        self.assertEqual(len(self.queue.automated_runs), 2)

    def test_en(self):
        self.queue.reset()
        self.assertEqual(len(self.queue.executed_runs), 0)

    def test_aliquot(self):
        self.queue.reset()
        a = self.queue.automated_runs[0]
        self.assertEqual(a.aliquot, 0)

if __name__ == '__main__':
    unittest.main()
