import math
import os
import unittest

from pychron.core.geometry.affine import transform_point, itransform_point
from pychron.stage.maps.laser_stage_map import LaserStageMap


class StageMapTestCase(unittest.TestCase):
    def setUp(self):
        p = 'pychron/stage/tests/data/221-hole.txt'
        if not os.path.isfile(p):
            p = './data/221-hole.txt'

        self.sm = LaserStageMap(file_path=p)

    def test_generate_interpolation(self):
        sm = self.sm
        h1 = sm.get_hole('1')
        h3 = sm.get_hole('3')
        h5 = sm.get_hole('5')

        h1.corrected = True
        h1.x_cor = 0
        h1.y_cor = 0

        h3.corrected = True
        h3.x_cor = 2
        h3.y_cor = 4

        h5.corrected = True
        h5.x_cor = 4
        h5.y_cor = 8

        sm.generate_row_interpolated_corrections()

        h2 = sm.get_hole('2')
        h4 = sm.get_hole('4')
        self.assertTupleEqual((1, 2, 3, 6),
                              (h2.x_cor, h2.y_cor,
                               h4.x_cor, h4.y_cor,))

    def test_generate_interpolation_no_mid(self):
        sm = self.sm
        h1 = sm.get_hole('1')
        h5 = sm.get_hole('5')

        h1.corrected = True
        h1.x_cor = 0
        h1.y_cor = 0

        h5.corrected = True
        h5.x_cor = 4
        h5.y_cor = 8

        sm.generate_row_interpolated_corrections()

        h2 = sm.get_hole('2')
        h4 = sm.get_hole('4')
        self.assertTupleEqual((1, 2, 3, 6),
                              (h2.x_cor, h2.y_cor,
                               h4.x_cor, h4.y_cor,))

    def test_generate_interpolation_no_end(self):
        sm = self.sm
        h1 = sm.get_hole('1')
        h3 = sm.get_hole('3')

        h1.corrected = True
        h1.x_cor = 0
        h1.y_cor = 0

        h3.corrected = True
        h3.x_cor = 2
        h3.y_cor = 4

        sm.generate_row_interpolated_corrections()

        h2 = sm.get_hole('2')
        h4 = sm.get_hole('4')
        self.assertTupleEqual((1, 2, 3, 6),
                              (h2.x_cor, h2.y_cor,
                               h4.x_cor, h4.y_cor,))

    def test_generate_interpolation_no_start(self):
        sm = self.sm
        h3 = sm.get_hole('3')
        h5 = sm.get_hole('5')

        h3.corrected = True
        h3.x_cor = 2
        h3.y_cor = 4

        h5.corrected = True
        h5.x_cor = 4
        h5.y_cor = 8

        sm.generate_row_interpolated_corrections()

        h2 = sm.get_hole('2')
        h4 = sm.get_hole('4')
        self.assertTupleEqual((1, 2, 3, 6),
                              (h2.x_cor, h2.y_cor,
                               h4.x_cor, h4.y_cor,))

    def test_generate_interpolation_no_points(self):
        sm = self.sm

        sm.generate_row_interpolated_corrections()

        h2 = sm.get_hole('2')
        h4 = sm.get_hole('4')
        self.assertTupleEqual((0, 0, 0, 0),
                              (h2.x_cor, h2.y_cor,
                               h4.x_cor, h4.y_cor,))

    def test_row_ends(self):
        holes = list(self.sm.row_ends())
        hs = [hi.id for hi in holes[:6]]

        self.assertListEqual(['1', '5', '6', '14', '15', '25'], hs)

    def test_row_ends2(self):
        holes = list(self.sm.row_ends(alternate=True))

        hs = [hi.id for hi in holes[:6]]

        self.assertListEqual(['1', '5', '14', '6', '15', '25'], hs)


class TransformTestCase(unittest.TestCase):
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
