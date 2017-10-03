import unittest

from numpy import linspace

from pychron.core.geometry.geometry import curvature


class CurvatureTestCase(unittest.TestCase):
    def test_line(self):

        xs = linspace(0,5)
        ys = 1*xs**2

        self.assertEqual(True, curvature(ys)[2])


if __name__ == '__main__':
    unittest.main()
