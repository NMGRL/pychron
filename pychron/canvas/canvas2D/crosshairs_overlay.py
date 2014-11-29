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
from chaco.abstract_overlay import AbstractOverlay
# ============= standard library imports ========================
# ============= local library imports  ==========================

class CrosshairsOverlay(AbstractOverlay):
    def overlay(self, component, gc, *args, **kw):
        with gc:
            comp = self.component

            if comp.crosshairs_kind == 'UserRadius':
                radius = comp.crosshairs_radius
            else:
                radius = comp.beam_radius

            sdp = comp.show_desired_position
            dp = comp.desired_position
            if sdp and dp is not None:
                self._draw_radius_ch(gc, dp, radius, color=comp.desired_position_color)

            if comp.show_laser_position:
                pos = (comp.x + (comp.x2 - comp.x) / 2.0, comp.y + (comp.y2 - comp.y) / 2.0)

                # add the offset
    #            print comp.crosshairs_offset, comp.crosshairs_offset is not (0, 0)
                if comp.crosshairs_offsetx or comp.crosshairs_offsety:
                    pos_off = pos[0] + comp.crosshairs_offsetx, pos[1] + comp.crosshairs_offsety
                    self._draw_radius_ch(gc, pos_off, radius, color=comp.crosshairs_offset_color, circle_only=True)

                self._draw_radius_ch(gc, pos, radius, color=comp.crosshairs_color)

    def _draw_simple_ch(self, gc, pt, length=4, color=None):
        if color is not None:
            gc.set_stroke_color(color)

        mx, my = pt
        gc.move_to(mx - length, my)
        gc.line_to(mx + length, my)
        gc.move_to(mx, my - length)
        gc.line_to(mx, my + length)
        gc.stroke_path()


    def _draw_radius_ch(self, gc, pt, radius, color=None, circle_only=False):
        if color is not None:
            rgb = lambda x: 0 <= x <= 1.
#            print color
            if not isinstance(color, (list, tuple)):
                color = color.toTuple()

            if not all(map(rgb, color)):
                f = lambda x:x / 255.
                color = map(f, color)

            gc.set_stroke_color(color)

        mx, my = pt
        mx += 1
        my += 1
        if radius:
            comp = self.component
            radius = comp._get_wh(radius, 0)[0]
            gc.arc(mx, my, radius, 0, 360)

            if not circle_only:
                x, x2, y, y2 = comp.x, comp.x2, comp.y, comp.y2
                gc.move_to(x, my)
                gc.line_to(mx - radius, my)

                gc.move_to(mx + radius, my)
                gc.line_to(x2, my)

                gc.move_to(mx, y)
                gc.line_to(mx, my - radius)
                gc.move_to(mx, my + radius)
                gc.line_to(mx, y2)
            gc.stroke_path()

        self._draw_simple_ch(gc, (mx, my), color=color)



# ============= EOF =============================================
