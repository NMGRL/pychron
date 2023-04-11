# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from __future__ import absolute_import

# ============= enthought library imports =======================
import math

from traits.api import List

from pychron.canvas.canvas2D.scene.primitives.base import Connectable
from pychron.canvas.canvas2D.scene.primitives.primitives import Bordered, Circle, Label
from pychron.canvas.canvas2D.scene.primitives.rounded import (
    RoundedRectangle,
    rounded_rect,
)


# ============= standard library imports ========================
# ============= local library imports  ==========================


class Switch(Connectable, Circle):
    associations = List

    def set_label(self, label, offset_x, offset_y, **kw):
        lb = Label(
            0,
            0,
            text=label,
            hjustify="center",
            soffset_x=offset_x,
            soffset_y=offset_y,
            # font='modern 9',
            use_border=False,
            **kw
        )

        self.primitives.append(lb)
        return lb

    def _render(self, gc):
        x, y = self.get_xy()
        r = self.radius
        r = self.map_dimension(r)

        if self.state:
            gc.set_fill_color(self._convert_color(self.active_color))
        else:
            gc.set_fill_color(self._convert_color(self.default_color))

        gc.arc(x + r, y + r / 2.0, r, 0, 360)
        gc.set_stroke_color((0, 0, 0))
        gc.set_line_width(2)
        gc.draw_path()

        for p in self.primitives:
            p.x, p.y = self.x, self.y
            p.render(gc)

    def is_in(self, sx, sy):
        x, y = self.get_xy()
        r = self.map_dimension(self.radius)
        return ((x + r - sx) ** 2 + (y + r / 2.0 - sy) ** 2) ** 0.5 < r


class BaseValve(Connectable):
    soft_lock = False
    owned = False
    oactive_color = (0, 255, 0)
    description = ""

    def toyaml(self):
        y = super(BaseValve, self).toyaml()
        del y["color"]
        del y["display_name"]
        del y["border_width"]
        del y["fill"]

        return y

    def get_tooltip_text(self):
        state = "Open" if self.state else "Closed"
        if self.soft_lock:
            state = "{}(Locked)".format(state)
        return "Valve={}\nDesc={}\nState={}".format(self.name, self.description, state)


class ManualSwitch(BaseValve, RoundedRectangle):
    width = 1.6622795630156608
    height = 2
    corner_radius = 4
    use_border_gaps = False

    def _rotate(self, gc, angle):
        x, y = self.get_xy()
        w, h = self.get_wh()
        xx = x + w / 2
        yy = y + h / 2.0
        gc.translate_ctm(xx, yy)
        gc.rotate_ctm(math.radians(angle))
        gc.translate_ctm(-xx, -yy)

    def _render_textbox(self, gc, *args, **kw):
        with gc:
            gc.translate_ctm(0, 25)
            super(ManualSwitch, self)._render_textbox(gc, *args, **kw)


class Valve(BaseValve, RoundedRectangle):
    width = 2
    height = 2
    corner_radius = 4
    use_border_gaps = False
    not_connected_color = (100, 100, 100)
    tag = "valve"

    def __init__(self, *args, **kw):
        super(Valve, self).__init__(*args, **kw)
        self.state = None

    def _get_border_color(self):
        c = self.get_color()
        c = [ci / 2.0 for ci in c]
        if len(c) == 4:
            c[3] = 1

        return c

    def set_stroke_color(self, gc):
        gc.set_stroke_color(self.get_color())

    def set_fill_color(self, gc):
        gc.set_fill_color(self.get_color())

    def get_color(self):
        if self.state is None:
            c = self._convert_color(self.not_connected_color)
        else:
            if self.state:
                c = self._convert_color(self.active_color)
            else:
                c = self._convert_color(self.default_color)

        return c

    def _render(self, gc):
        x, y = self.get_xy(clear_layout_needed=False)
        w, h = self.get_wh()
        super(Valve, self)._render(gc)

        self._draw_soft_lock(gc)

        self._draw_owned(gc)
        self._draw_state_indicator(gc, x, y, w, h)

    def _draw_soft_lock(self, gc):
        if self.soft_lock:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color((0, 0, 1))
                gc.set_line_width(5)

                x, y = self.get_xy()
                width, height = self.get_wh()
                corner_radius = 3
                rounded_rect(gc, x, y, width, height, corner_radius)

    def _draw_owned(self, gc):
        if self.owned:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color((0, 0, 0))
                gc.set_line_width(5)

                x, y = self.get_xy()
                width, height = self.get_wh()
                corner_radius = 3
                rounded_rect(gc, x, y, width, height, corner_radius)

    def _draw_state_indicator(self, gc, x, y, w, h):
        if not self.state:
            gc.set_stroke_color((0, 0, 0))
            l = 5
            o = 2
            gc.set_line_width(2)
            with gc:
                gc.translate_ctm(x, y)

                # lower left
                gc.move_to(o, o)
                gc.line_to(o + l, o + l)

                # upper left
                gc.move_to(o, h - o)
                gc.line_to(o + l, h - o - l)

                # lower right
                gc.move_to(w - o, o)
                gc.line_to(w - o - l, o + l)

                # upper left
                gc.move_to(w - o, h - o)
                gc.line_to(w - o - l, h - o - l)
                gc.draw_path()


def rounded_triangle(gc, cx, cy, width, height, cr):
    w2 = width / 2.0
    gc.translate_ctm(cx + cr / 3, cy)

    gc.begin_path()
    gc.move_to(w2, 0)
    gc.arc_to(width, 0, width - cr, cr, cr)
    gc.arc_to(w2, height + cr, w2 - cr, height, cr)
    gc.arc_to(0, 0, cr, 0, cr)
    gc.line_to(w2, 0)
    gc.draw_path()


class RoughValve(BaseValve, Bordered):
    width = 3
    height = 2
    border_width = 3

    def _render(self, gc):
        cx, cy = self.get_xy(clear_layout_needed=False)
        #         cx, cy = 200, 50
        width, height = self.get_wh()
        #         width += 10
        cr = 4
        func = lambda: rounded_triangle(gc, cx, cy, width, height, cr)
        if self.use_border:
            with gc:
                gc.set_line_width(self.border_width)
                c = self._get_border_color()
                gc.set_stroke_color(c)
                func()
                #                 rounded_triangle(gc, cx, cy, width, height, cr)
        else:
            func()

        self._draw_state_indicator(gc, cx, cy, width, height, cr)
        self._render_name(gc, cx, cy, width, height)
        self._draw_owned(gc, func)
        self._draw_soft_lock(gc, func)

    def _draw_owned(self, gc, func):
        if self.owned:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color((0, 0, 1))
                gc.set_line_width(5)
                func()
                gc.draw_path()

    def _draw_soft_lock(self, gc, func):
        if self.soft_lock:
            with gc:
                gc.set_fill_color((0, 0, 1, 0))
                gc.set_stroke_color((0, 0, 1))
                gc.set_line_width(5)
                func()
                gc.draw_path()

    def _draw_state_indicator(self, gc, x, y, w, h, cr):
        if not self.state:
            with gc:
                gc.translate_ctm(x, y)
                gc.set_line_width(2)
                gc.set_stroke_color((0, 0, 0, 1))

                l = 6
                o = 2

                # lower left
                gc.move_to(o + cr, o)
                gc.line_to(o + cr + l, o + l - 3)

                # lower right
                gc.move_to(w - o - cr, o)
                gc.line_to(w - o - cr - l, o + l - 3)

                # upper center
                w2 = w / 2.0 + 1
                gc.move_to(w2, h)
                gc.line_to(w2, h - l)

                gc.draw_path()


# class RoughValve2(BaseValve):
#     def _render_(self, gc):
#         cx, cy = self.get_xy()
#         width, height = self.get_wh()
#
#         w2 = width / 2
#         x1 = cx
#         x2 = cx + width
#         x3 = cx + w2
#
#         y1 = cy
#         y2 = y1
#         y3 = cy + height
#
#         gc.lines([(x1, y1), (x2, y2), (x3, y3), (x1, y1)])
#         gc.fill_path()
#
#         #         gc.set_stroke_color((0, 0, 0))
#         #         gc.lines([(x1, y1), (x2, y2), (x3, y3), (x1, y1)])
#
#
#         #         func = gc.lines
#         #         args = (([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x2, y2)]),)
#         #        args = (x - 2, y - 2, width + 4, height + 4)
#
#         #         self._draw_soft_lock(gc, func, args)
#         #         self._draw_owned(gc, func, args)
#         self._draw_state_indicator(gc, cx, cy, width, height)
#         self._render_name(gc, cx, cy, width, height)
#
#     def _draw_owned(self, gc, func, args):
#         if self.soft_lock:
#             with gc:
#                 gc.set_fill_color((0, 0, 0, 0))
#                 gc.set_stroke_color((0, 0, 1))
#                 gc.set_line_width(5)
#                 func(*args)
#                 gc.draw_path()
#
#     def _draw_soft_lock(self, gc, func, args):
#         if self.soft_lock:
#             with gc:
#                 gc.set_fill_color((0, 0, 1, 0))
#                 gc.set_stroke_color((0, 0, 1))
#                 gc.set_line_width(5)
#                 func(*args)
#                 gc.draw_path()
#
#     def _draw_state_indicator(self, gc, x, y, w, h):
#         if not self.state:
#             l = 7
#             w2 = w / 2.
#             w3 = w / 3.
#
#             gc.set_line_width(2)
#             gc.move_to(x + w2, y + h)
#             gc.line_to(x + w2, y + h - l)
#             gc.draw_path()
#
#             gc.move_to(x, y)
#             gc.line_to(x + w3, y + l)
#             gc.draw_path()
#
#             gc.move_to(x + w, y)
#             gc.line_to(x + w - w3, y + l)
#             gc.draw_path()

# ============= EOF =============================================
