#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Float, on_trait_change, Bool, Property, List
from traitsui.api import  Item, VGroup, HGroup
from pychron.canvas.canvas2D.scene.primitives.primitives import Point, Polygon, \
    PolyLine, PointIndicator, Line
from pychron.geometry.geometry import calc_point_along_line
#============= standard library imports ========================
#============= local library imports  ==========================
class VelocityPolyLine(PolyLine):
    velocity_segments = List

class LaserPoint(PointIndicator):
    z = Float
    mask = Float
    attenuator = Float
    calibrated_x = Float
    calibrated_y = Float

class DrillPoint(LaserPoint):
    velocity = Float
    zend = Float

class RasterPolygon(Polygon):
    use_convex_hull = Bool(False)
    use_outline = Bool(True)
    offset = Float(1, enter_set=True, auto_set=False)

    velocity = Float
    find_min = Bool(True)
    theta = Property(Float(enter_set=True, auto_set=False),
                     depends_on='_theta')
    _theta = Float

    def _set_theta(self, v):
        self._theta = float(v)
        self.request_redraw()

    def _get_theta(self):
        return self._theta

    def _find_min_changed(self):
        self._theta = 0
        self.request_redraw()

    @on_trait_change('offset, use_outline')
    def _refresh(self):
        self.request_redraw()

    def _get_group(self):
        g = VGroup(HGroup(Item('use_outline'),
                          Item('offset'),
                          ),
                   HGroup(Item('find_min'),
                          Item('theta')
                          )
                   )

        return g

class Transect(PolyLine):
    step = Float
    step_points = List
    _cached_ptargs = None
    point_klass = LaserPoint

    def add_point(self, x, y, z=0, point_color=(1, 0, 0), line_color=(1, 0, 0),
                   **ptargs):

        p2 = LaserPoint(x, y, z=z, default_color=point_color, **ptargs)
        self._add_point(p2, line_color)

    def get_point(self, p):
        if p == 0:
            return self.points[0]

        if p <= len(self.step_points):
            return self.step_points[p - 1]

    def _get_group(self):
        g = Item('step', label='Step (units)')
        return g

    def set_step_points(self, **ptargs):
        self.step_points = []
        self._cached_ptargs = ptargs
        self._set_transect_points(**ptargs)
        self.request_redraw()

    def _step_changed(self):
        if self.step:
            ptargs = self._cached_ptargs
            if ptargs is None:
                ptargs = dict()
            self.set_step_points(**ptargs)

    def _set_transect_points(self, line_color=None, point_color=(1, 0, 0), **ptargs):
        if line_color is None:
            line_color = (1, 0, 0)
        if point_color is None:
            point_color = (1, 0, 0)

        step = self.step
        cnt = 1
        for li in self.lines:
            p1 = li.start_point
            p2 = li.end_point

#            if cnt is None:
#                cnt = int(p1.identifier) + 1

            x, y = p1.x, p1.y

            tol = step / 3.
            while 1:
                x, y = calc_point_along_line(x, y, p2.x, p2.y, step)
                ptargs['use_border'] = False
                if abs(p2.x - x) < tol and abs(p2.y - y) < tol:
                    p = self.new_point(p2.x, p2.y, cnt, **ptargs)
                    self.step_points.append(p)
                    cnt += 1
                    break
                else:
                    p = self.new_point(x, y,
                                       cnt,
                                   line_color=line_color, point_color=point_color,
                                   **ptargs)


                    self.step_points.append(p)
                    cnt += 1

    def new_point(self, x, y, i, **kw):
        p = LaserPoint(x, y,
                identifier=str(i),
                **kw
                )
        return p

    def set_canvas(self, canvas):
#        self.canvas = canvas
        super(Transect, self).set_canvas(canvas)
        for pt in self.step_points:
            pt.set_canvas(canvas)

    def _render_(self, gc):
        super(Transect, self)._render_(gc)
        for si in self.step_points:
            si.render(gc)

#============= EOF =============================================
