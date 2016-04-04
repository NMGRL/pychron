import unittest

from pychron.canvas.canvas2D.scene.primitives.primitives import CalibrationObject


class CalibrationObjectTestCase(unittest.TestCase):
    def setUp(self):
        self._cal_obj = CalibrationObject(cx=0, cy=0)

    def test_calc_rotation_east_counter_clockwise(self):
        rot = self._cal_obj.calculate_rotation(1, 1)
        self.assertEqual(rot, 45.0)

    def test_calc_rotation_west_counter_clockwise(self):
        rot = self._cal_obj.calculate_rotation(-1, -1, 'west')
        self.assertEqual(rot, 45.0)

    def test_calc_rotation_south_counter_clockwise(self):
        rot = self._cal_obj.calculate_rotation(1, -1, 'south')
        self.assertEqual(rot, 45.0)

    def test_calc_rotation_north_counter_clockwise(self):
        rot = self._cal_obj.calculate_rotation(-1, 1, 'north')
        self.assertEqual(rot, 45.0)

    def test_calc_rotation_east_clockwise(self):
        rot = self._cal_obj.calculate_rotation(1, -1)
        self.assertEqual(rot, -45.0)

    def test_calc_rotation_west_clockwise(self):
        rot = self._cal_obj.calculate_rotation(-1, 1, 'west')
        self.assertEqual(rot, -45.0)

    def test_calc_rotation_south_clockwise(self):
        rot = self._cal_obj.calculate_rotation(-1, -1, 'south')
        self.assertEqual(rot, -45.0)

    def test_calc_rotation_north_clockwise(self):
        rot = self._cal_obj.calculate_rotation(1, 1, 'north')
        self.assertEqual(rot, -45.0)


if __name__ == '__main__':
    unittest.main()
