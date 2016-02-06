from pychron.core.stats.peak_detection import find_peaks
from pychron.core.stats.probability_curves import cumulative_probability

__author__ = 'ross'

import unittest


class MultiPeakDetectionTestCase(unittest.TestCase):
    def setUp(self):
        xs = [10, 10, 10, 20, 20, 20]
        es = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        self.xs, self.ys = cumulative_probability(xs, es, 5, 25)

    def test_find_min_peaks(self):
        maxp, minp = find_peaks(self.ys, self.xs, lookahead=1)
        self.assertEqual(len(minp), 1)

    def test_find_max_peaks(self):
        maxp, minp = find_peaks(self.ys, self.xs, lookahead=1)
        self.assertEqual(len(maxp), 2)

    def test_max_peak_x(self):
        maxp, minp = find_peaks(self.ys, self.xs, lookahead=1)
        self.assertAlmostEqual(maxp[0][0], 10.0, 0)

    def test_max_peak_x2(self):
        maxp, minp = find_peaks(self.ys, self.xs, lookahead=1)
        self.assertAlmostEqual(maxp[1][0], 20.0, 0)


if __name__ == '__main__':
    unittest.main()
