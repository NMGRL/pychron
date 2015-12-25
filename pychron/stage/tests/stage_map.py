import math
import unittest

from pychron.core.geometry.affine import transform_point, itransform_point


class StageMapTestCase(unittest.TestCase):
    def test_itransform_point_ntran_nrot(self):
        cpos = 0, 0
        rot = 0

        pt = 1, 1
        tpt = itransform_point(pt, cpos, rot, 1)
        self.assertAlmostEqual(pt, tpt)

    def test_itransform_point_nrot(self):
        cpos = 1, 0
        rot = 0

        pt = 2, 1
        tpt = itransform_point(pt, cpos, rot, 1)
        self.assertTupleEqual((1.0, 1.0), tpt)

    def test_itransform_point(self):
        cpos = 1, 0
        rot = 90

        pt = 1, 1
        tpt = itransform_point(pt, cpos, rot, 1)

        self.assertAlmostEqual(1.0, tpt[0])
        self.assertAlmostEqual(0, tpt[1])

    def test_transform_point_ntran_nrot(self):
        cpos = 0, 0
        rot = 0

        pt = 1, 1
        tpt = transform_point(pt, cpos, rot, 1)
        self.assertAlmostEqual(pt, tpt)

    def test_transform_point_nrot(self):
        cpos = 1, 0
        rot = 0

        pt = 1, 1
        tpt = transform_point(pt, cpos, rot, 1)
        self.assertTupleEqual((2.0, 1.0), tpt)

    def test_transform_point_ntrans(self):
        cpos = 0, 0
        rot = 90

        pt = 1, 0
        tpt = transform_point(pt, cpos, rot, 1)

        self.assertAlmostEqual(0.0, tpt[0])
        self.assertAlmostEqual(1.0, tpt[1])

    def test_transform_point(self):
        cpos = 1, 0
        rot = 90

        pt = 1, 0
        tpt = transform_point(pt, cpos, rot, 1)

        self.assertAlmostEqual(1.0, tpt[0])
        self.assertAlmostEqual(1.0, tpt[1])

    def test_transform_point2(self):
        cpos = 0, 0
        rot = 45

        pt = 1, 0
        tpt = transform_point(pt, cpos, rot, 1)

        r2 = 0.5 ** 0.5
        self.assertAlmostEqual(r2, tpt[0])
        self.assertAlmostEqual(r2, tpt[1])

    def test_transform_point3(self):
        cpos = 1.5, -1.5
        rot = 45

        pt = 1, 0
        tpt = transform_point(pt, cpos, rot, 1)

        r2 = 0.5 ** 0.5
        self.assertAlmostEqual(1.5 + r2, tpt[0])
        self.assertAlmostEqual(-1.5 + r2, tpt[1])

    def test_transform_point4(self):
        cpos = -2.1, -0.3
        rot = 1
        t = math.radians(rot)

        pt = 1, 0
        tpt = transform_point(pt, cpos, rot, 1)

        x = pt[0] * math.cos(t) - pt[1] * math.sin(t)
        y = pt[0] * math.sin(t) + pt[1] * math.cos(t)

        self.assertAlmostEqual(-2.1 + x, tpt[0])
        self.assertAlmostEqual(-0.3 + y, tpt[1])


if __name__ == '__main__':
    unittest.main()
