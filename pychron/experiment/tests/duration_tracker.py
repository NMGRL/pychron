import os
import unittest

from pychron.experiment.stats import AutomatedRunDurationTracker
from pychron.paths import paths


class MockRun:
    def __init__(self, r, sh, sht):
        self.spec = MockSpec(r, sh, sht)
        if sh != sht:
            self.spec._truncated = True


class MockSpec:
    _truncated = False

    def __init__(self, runid, script_hash, script_hash_truncated):
        self.script_hash_truncated = script_hash_truncated
        self.script_hash = script_hash
        self.runid = runid

    def is_truncated(self):
        return self._truncated


class DurationTrackerTestCase(unittest.TestCase):
    def setUp(self):
        paths.build('_dt')
        self.dt = AutomatedRunDurationTracker()

    def tearDown(self):
        os.remove(paths.duration_tracker)
        os.remove(paths.duration_tracker_frequencies)

    def test_prob(self):
        run = MockRun('1000-01', 'a', 'a')
        self.dt.update(run, 10)
        run = MockRun('1000-01', 'a', 'b')
        self.dt.update(run, 1)
        self.dt.update(run, 1)

        prob = self.dt._frequencies['a']
        self.assertEqual(prob, 2 / 3.)

    def test_prob2(self):
        run = MockRun('1000-01', 'a', 'a')
        self.dt.update(run, 10)
        run = MockRun('1000-01', 'a', 'b')
        self.dt.update(run, 1)
        self.dt.update(run, 1)
        self.dt.update(run, 1)

        prob = self.dt._frequencies['a']
        self.assertEqual(prob, 3 / 4.)

    def test_pm(self):
        run = MockRun('1000-01', 'a', 'a')
        self.dt.update(run, 10)
        run = MockRun('1000-01', 'a', 'b')
        self.dt.update(run, 1)
        self.dt.update(run, 1)
        self.dt.update(run, 1)
        n = 2e4
        ds = [self.dt.probability_model('a', 'b') for i in xrange(int(n))]
        nt = ds.count(1)

        self.assertAlmostEqual(nt / float(n), 0.75, 2)


if __name__ == '__main__':
    unittest.main()
