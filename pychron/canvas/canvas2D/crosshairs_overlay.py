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
from chaco.abstract_overlay import AbstractOverlay
from kiva import Font
from kiva.trait_defs.kiva_font_trait import KivaFont
from traits.api import Float, Enum, Bool


# ============= standard library imports ========================
# ============= local library imports  ==========================


class SimpleCrosshairsOverlay(AbstractOverlay):
    radius = Float
    constrain = Enum('', 'x', 'y')
    circle_only = Bool(True)

    def overlay(self, component, gc, *args, **kw):
        with gc:
            gc.clip_to_rect(component.x, component.y,
                            component.width, component.height)
            comp = self.component

            sdp = comp.show_desired_position
            dp = comp.desired_position
            if sdp and dp is not None:
                self._draw_radius_ch(gc, component, dp, self.radius,
                                     color=comp.desired_position_color)

            if comp.show_current_position:
                pos = comp.stage_position
                self._draw_radius_ch(gc, component, pos, self.radius,
                                     color=comp.crosshairs_color)

    def _draw_simple_ch(self, gc, pt, length=4, color=None):
        if color is not None:
            gc.set_stroke_color(color)

        mx, my = pt
        gc.set_line_width(self.component.crosshairs_line_width)
        gc.move_to(mx - length, my)
        gc.line_to(mx + length, my)
        gc.move_to(mx, my - length)
        gc.line_to(mx, my + length)
        gc.stroke_path()

    def set_color(self, gc, color, stroke=True, fill=False):
        if color is not None:
            if not isinstance(color, (list, tuple)):
                color = color.red(), color.green(), color.blue(), color.alpha()

            if not all([0 <= xx <= 1. for xx in color]):
                color = [xx / 255. for xx in color]
            if stroke:
                gc.set_stroke_color(color)

            if fill:
                gc.set_fill_color(color)

        return color

    def _draw_radius_ch(self, gc, component, pt, radius, color=None, circle_only=False):
        if color:
            color = self.set_color(gc, color)


        mx, my = pt
        if self.constrain == 'x':
            sx, sy = component.map_screen([(0, 0)])[0]
            mx = sx
        elif self.constrain == 'y':
            sx, sy = component.map_screen([(0, 0)])[0]
            my = sy

        # mx += 1
        # my += 1
        if radius:
            # radius = component.get_wh(radius, 0)[0]
            gc.set_line_width(self.component.crosshairs_line_width)
            gc.arc(mx, my, radius, 0, 360)

            if not self.circle_only or not circle_only:
                x, x2, y, y2 = component.x, component.x2, \
                               component.y, component.y2
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


class CrosshairsOverlay(SimpleCrosshairsOverlay):
    circle_only = False
    font = KivaFont("modern 10")

    def overlay(self, component, gc, *args, **kw):
        with gc:
            gc.clip_to_rect(component.x, component.y,
                            component.width, component.height)
            # if component.crosshairs_kind == 'UserRadius':
            #     radius = component.crosshairs_radius
            # else:
            #     radius = component.beam_radius
            #
            # radius = component.get_wh(radius, 0)[0]
            radius = component.get_crosshairs_radius(screen=True)
            sdp = component.show_desired_position
            dp = component.desired_position

            # get offset in screen space
            ox, oy = component.get_screen_offset()
            if sdp and dp is not None:
                pos_off = dp[0] + ox, dp[1] + oy
                self._draw_radius_ch(gc, component, pos_off, radius,
                                     color=component.desired_position_color)

            mx = component.x + (component.x2 - component.x) / 2.0
            my = component.y + (component.y2 - component.y) / 2.0
            if component.show_laser_position:
                if ox or oy:
                    pos_off = mx + ox, my + oy
                    self._draw_radius_ch(gc, component, pos_off, radius,
                                         color=component.crosshairs_offset_color)
                else:
                    self._draw_radius_ch(gc, component, (mx, my), radius,
                                         color=component.crosshairs_color)

            if component.show_hole_label:
                h = component.get_current_hole()
                if h is not None:
                    x, y = mx + ox + radius, my + oy + radius
                    color = component.hole_label_color
                    self.set_color(gc, color, fill=True)

                    gc.set_text_position(x, y)
                    gc.set_font(self.component.hole_label_font)
                    gc.show_text(h.id)

# ============= EOF ============================================
