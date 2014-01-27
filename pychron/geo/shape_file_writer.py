#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
import os
import shapefile

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.loggable import Loggable


class ShapeFileWriter(Loggable):
    def write_points(self, p, points, attrs=None, epsg=None):
        """
            points: list of Point objects
            if epsg is not None write a .prj file

        """
        writer=shapefile.Writer(shapefile.POINT)

        if attrs:
            #register attrs as fields
            for ai in attrs:
                writer.field(ai)

        for pp in points:
            writer.point(pp.x, pp.y)
            if attrs:
                d=dict([(ai, getattr(pp, ai)) for ai in attrs])
                writer.record(**d)

        writer.save(p)
        if epsg:
            self.write_prj(p, epsg)

        return True

    def write_prj(self, p, epsg):
        import urllib

        head, tail=os.path.splitext(p)
        p='{}.prj'.format(head)

        with open(p, 'w') as fp:
            ref="http://spatialreference.org/ref/epsg/{}/prettywkt/".format(epsg)
            f=urllib.urlopen(ref)
            fp.write(f.read())

    def write_polygon(self, p, polygons):
        """
            polygons: list of Polygon objects

            Polygon.points=[[x0,y0],...,[xN,yN]]
        """
        writer = shapefile.Writer(shapefile.POLYGON)
        for pp in polygons:
            writer.poly(parts=[pp.points])

        writer.save(p)



#============= EOF =============================================

