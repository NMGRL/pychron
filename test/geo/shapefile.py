from pychron.core.ui import set_toolkit
from pychron.geo.primitives import AgePoint

set_toolkit('qt4')

import os
from pychron.geo.shape_file_writer import ShapeFileWriter
from pychron.paths import paths

__author__ = 'ross'

import unittest
from pyproj import Proj, transform



class ShapefileWriterestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_path = os.path.join(paths.disseration, 'data', 'minnabluff', 'gis', 'test_points.shp')
        cls.points = [AgePoint(sample=a, y=b, x=c)
                      for a, b, c in [('MB07-186', -78.5323888889, 166.268833333),
                                      ('MB07-025', -78.6664444444, 167.099638889),
                                      ('MB07-017', -78.6634722222, 167.058055556),
                                      ('MB07-045', -78.5511666667, 166.652138889),
                                      ('MB07-068', -78.5105833333, 165.909722222),
                                      ('MB07-114', -78.6471111111, 167.082416667),
                                      ('MB07-122', -78.4094444444, 165.491694444),
                                      ('MB07-133', -78.5890277778, 166.968833333),
                                      ('MB07-136', -78.5886944444, 166.969638889),
                                      ('MB07-144', -78.5860277778, 166.973416667)]]

        p1 = Proj(proj='latlong', datum='WGS84')
        p2 = Proj(init='epsg:3031')
        for pp in cls.points:
            x, y=transform(p1, p2, pp.x, pp.y)
            pp.x=x
            pp.y=y

    # def test_projection(self):
    #     from pyproj import Proj, transform
    #     latlong=Proj(proj='latlong', datum='WGS84')
    #     utm=Proj(init='epsg:3031')
    #
    #     pt=self.points[0]
    #
    #     x, y=transform(latlong, utm, pt.x, pt.y)
    #     self.assertEqual(y, 290000)

    def test_something(self):
        writer = ShapeFileWriter()
        p=self.test_path
        if os.path.isfile(p):
            os.unlink(p)

        writer.write_points(p, points=self.points,
                            attrs=('sample', 'material','age', 'age_error'))

        self.assertTrue(os.path.isfile(p))


    def test_write_prj(self):
        epsg='3031'
        writer = ShapeFileWriter()
        writer.write_prj(self.test_path, epsg)

        head, _=os.path.splitext(self.test_path)
        p='{}.prj'.format(head)
        self.assertTrue(os.path.isfile(p))


if __name__ == '__main__':
    unittest.main()
