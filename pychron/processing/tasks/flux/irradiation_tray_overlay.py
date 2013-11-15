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
from chaco.abstract_overlay import AbstractOverlay

#============= standard library imports ========================
from numpy import linspace, hstack, vstack, array
#============= local library imports  ==========================

class IrradiationTrayOverlay(AbstractOverlay):
    _cached_pts = None

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            comp = self.component
            gc.clip_to_rect(comp.x, comp.y, comp.width, comp.height)
            gc.set_fill_color((1, 0, 1))
            if self._cached_pts is None:
                self._cached_pts = self._gather_points()

            for x, y, pts in self._cached_pts:
                self._render_hole(gc, x, y, pts)

            gc.stroke_path()

    def do_layout(self):
        super(IrradiationTrayOverlay, self).do_layout()
        self._cached_pts = None


    def _render_hole(self, gc, x, y, pts):
        with gc:
            #print x, y
            gc.translate_ctm(x, y)
            gc.lines(pts)
            #gc.rect(0,0,10,10)
            #gc.draw_path()
            #gc.stroke_path()

    def _gather_points(self):
        pts = []
        for x, y, r in self.geometry:
            rw, ow = self.component.index_mapper.map_screen(array([r, 0]))
            rh, oh = self.component.value_mapper.map_screen(array([r, 0]))
            x, y = self.component.map_screen([(x, y), ])[0]
            rw = rw - ow
            rh = rh - oh

            xs = linspace(-rw, rw, 50)
            xs2 = linspace(rw, -rw, 50)

            ys = rh * ((1 - (xs / rw) ** 2)) ** 0.5
            ys2 = -rh * ((1 - (xs2 / rw) ** 2)) ** 0.5

            xs = hstack((xs, xs2))
            ys = hstack((ys, ys2))
            pt = vstack((xs, ys)).T
            pts.append((x, y, pt))
        return pts


#============= EOF =============================================
