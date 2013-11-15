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
from traits.api import List, on_trait_change

from pychron.canvas.canvas2D.scene.primitives.primitives import rounded_rect, \
    RoundedRectangle, QPrimitive, Bordered, Connectable
#============= standard library imports ========================
#============= local library imports  ==========================


class BaseValve(Connectable):
    soft_lock = False
    owned = False
    oactive_color = (0, 255, 0)

    def is_in(self, x, y):
        mx, my = self.get_xy()
        w, h = self.get_wh()
        if mx <= x <= (mx + w) and my <= y <= (my + h):
            return True


class Valve(RoundedRectangle, BaseValve):
    width = 2
    height = 2
    corner_radius = 4

    def _render_(self, gc):

        super(Valve, self)._render_(gc)
        #
        x, y = self.get_xy()
        w, h = self.get_wh()

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
            l = 7
            o = 2
            gc.set_line_width(2)
            gc.move_to(x + o, y + o)
            gc.line_to(x + l, y + l)

            gc.move_to(x + o, y - o + h)
            gc.line_to(x + o + l, y - o + h - l)

            gc.move_to(x - o + w, y - o + h)
            gc.line_to(x - o + w - l, y - o + h - l)

            gc.move_to(x - o + w, y + o)
            gc.line_to(x - o + w - l, y + o + l)
            gc.draw_path()


def rounded_triangle(gc, cx, cy, width, height, cr):
    w2 = width / 2.
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

    def _render_(self, gc):
        cx, cy = self.get_xy()
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
                gc.set_stroke_color((0, 0, 0, 1))

                l = 6
                w2 = w / 2.
                w3 = w / 3.

                gc.set_line_width(2)
                gc.move_to(x + w2, y + h - 1)
                gc.line_to(x + w2, y + h - l)
                gc.draw_path()

                gc.move_to(x + cr, y + cr / 2.)
                gc.line_to(x + cr + w3, y + l)
                gc.draw_path()

                gc.move_to(x + w - cr, y + cr / 2.)
                gc.line_to(x + w - cr - w3, y + l)
                gc.draw_path()


class RoughValve2(BaseValve):
    def _render_(self, gc):
        cx, cy = self.get_xy()
        width, height = self.get_wh()

        w2 = width / 2
        x1 = cx
        x2 = cx + width
        x3 = cx + w2

        y1 = cy
        y2 = y1
        y3 = cy + height

        gc.lines([(x1, y1), (x2, y2), (x3, y3), (x1, y1)])
        gc.fill_path()

        #         gc.set_stroke_color((0, 0, 0))
        #         gc.lines([(x1, y1), (x2, y2), (x3, y3), (x1, y1)])


        #         func = gc.lines
        #         args = (([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x2, y2)]),)
        #        args = (x - 2, y - 2, width + 4, height + 4)

        #         self._draw_soft_lock(gc, func, args)
        #         self._draw_owned(gc, func, args)
        self._draw_state_indicator(gc, cx, cy, width, height)
        self._render_name(gc, cx, cy, width, height)

    def _draw_owned(self, gc, func, args):
        if self.soft_lock:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color((0, 0, 1))
                gc.set_line_width(5)
                func(*args)
                gc.draw_path()

    def _draw_soft_lock(self, gc, func, args):
        if self.soft_lock:
            with gc:
                gc.set_fill_color((0, 0, 1, 0))
                gc.set_stroke_color((0, 0, 1))
                gc.set_line_width(5)
                func(*args)
                gc.draw_path()

    def _draw_state_indicator(self, gc, x, y, w, h):
        if not self.state:
            l = 7
            w2 = w / 2.
            w3 = w / 3.

            gc.set_line_width(2)
            gc.move_to(x + w2, y + h)
            gc.line_to(x + w2, y + h - l)
            gc.draw_path()

            gc.move_to(x, y)
            gc.line_to(x + w3, y + l)
            gc.draw_path()

            gc.move_to(x + w, y)
            gc.line_to(x + w - w3, y + l)
            gc.draw_path()

#============= EOF =============================================
