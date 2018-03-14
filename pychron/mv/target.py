# ===============================================================================
# Copyright 2012 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import
from traits.api import HasTraits, cached_property, Property, Tuple, Any, Float


# ============= standard library imports ========================
# from numpy import array
# ============= local library imports  ==========================
# from pychron.core.geometry.convex_hull import convex_hull_area
# from pychron.core.geometry.centroid import calculate_centroid
# from pychron.core.codetools.simple_timeit import timethis
# from pychron.core.geometry.convex_hull import convex_hull_area
# from pychron.core.geometry.centroid.calculate_centroid import calculate_centroid

class Target:
    poly_points = None
    bounding_rect = None
    #    threshold = None
    area = 0
    convex_hull_area = 0
    origin = None
    centroid = None
    min_enclose_area = 0
    pactual = 0
    pconvex_hull = 0

    @property
    def dev_centroid(self):
        return ((self.origin[0] - self.centroid[0]),
                (self.origin[1] - self.centroid[1]))

    @property
    def aspect_ratio(self):
        return self.bounding_rect.width / float(self.bounding_rect.height)

    @property
    def convexity(self):
        # return True
        return self.area / self.min_enclose_area

    @property
    def perimeter_convexity(self):
        return self.pconvex_hull / self.pactual

        #        return self.
        #        r = timethis(convex_hull_area, args=(self.poly_points,))

        #        return self.area / convex_hull_area()
        #        return self.area / convex_hull_area(self.poly_points)

        #    @cached_property
        #    def _get_centroid(self):
        # #        pts = array([(pt.x, pt.y) for pt in self.poly_points], dtype=float)
        # #        v = timethis(calculate_centroid, args=(self.poly_points,))
        #        return calculate_centroid(self.poly_points)
        # #        print v
        #        return v

        #    @property

# def dev_br(self):
#        return ((self.origin[0] - self.bounding_rect[0]),
#                (self.origin[1] - self.bounding_rect[1]))
#    @property
#    def bounding_area(self):
#        return self.bounding_rect[1] ** 2 * 3.1415
#        print self.bounding_rect
#        return 1
#        return self.bounding_rect[2] * self.bounding_rect[3]

# ============= EOF =============================================
