from pychron.core.stats.peak_detection import find_peaks, find_fine_peak
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


class FinePeakDetectionTestCase(unittest.TestCase):
    def setUp(self):
        self.xs = [10, 10, 10]
        self.es = [0.1, 0.1, 0.1]

    def test_fine_peak(self):
        p = find_fine_peak(lambda mi, ma: cumulative_probability(self.xs, self.es, mi, ma, n=500),
                           tol=0.0001, initial_limits=(5, 15), lookahead=1)
        self.assertAlmostEqual(p, 10, 5)


if __name__ == '__main__':
    unittest.main()
