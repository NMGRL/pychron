# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.base import QPrimitive
from pychron.canvas.canvas2D.scene.primitives.primitives import Point, Bordered, BorderLine


def fork(gc, lx, ly, rx, ry, mx, my, h):
    # draw left prong
    gc.move_to(lx, ly)
    gc.line_to(lx, ly + h)

    # draw right prong
    gc.move_to(rx, ry)
    gc.line_to(rx, ry + h)

    # draw connector
    gc.move_to(lx - 5, ly + h - 5)
    gc.line_to(rx + 5, ly + h - 5)

    # draw handle
    gc.move_to(mx, ly + h)
    gc.line_to(mx, my)
    gc.draw_path()


class Fork(QPrimitive, Bordered):
    left = None
    right = None
    mid = None
    height = 10
    inverted = False

    def get_midx(self):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        return lx + (rx - lx) / 2.

    def set_points(self, lx, ly, rx, ry, mx, my):
        self.left = Point(lx, ly)
        self.right = Point(rx, ry)
        self.mid = Point(mx, my)

        self.inverted = my > ly

    def set_canvas(self, canvas):
        self.left.set_canvas(canvas)
        self.right.set_canvas(canvas)
        self.mid.set_canvas(canvas)
        super(Fork, self).set_canvas(canvas)

    def _render_(self, gc):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        mx, my = self.mid.get_xy()
        # ly, ry = ly - 30, ry - 30
        mx = lx + (rx - lx) / 2.

        w, h = self.get_wh()
        # print self.height, h, self.canvas
        # M
        # |
        # _|_
        # |   |
        # L   R
        with gc:
            gc.set_line_width(20)
            gc.set_stroke_color(self._get_border_color())

            # gc.set_line_width(5)
            # fill in corners
            gc.move_to(lx - 10, ly + h - 5)
            gc.line_to(rx + 10, ly + h - 5)

            fork(gc, lx, ly, rx, ry, mx, my, h)

        gc.set_line_width(10)
        # self.set_fill_color(gc)
        fork(gc, lx, ly, rx, ry, mx, my, h)


def tee_h(gc, x1, y1, x2, my, y2):
    # draw main horizontal
    gc.move_to(x1, my)
    gc.line_to(x2, my)
    # draw vertical
    gc.move_to(x1, y1)
    gc.line_to(x1, y2)
    gc.draw_path()


def tee_v(gc, x1, y1, x2, mx, y2):
    # draw main horizontal
    gc.move_to(x1, y1)
    gc.line_to(x2, y1)
    # draw vertical
    gc.move_to(mx, y1)
    gc.line_to(mx, y2)
    gc.draw_path()


class Tee(Fork):
    def _render_(self, gc):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        mx, my = self.mid.get_xy()
        # ly, ry = ly - 30, ry - 30
        if ly == ry:
            self._render_vertical(gc, lx, ly, rx, ry, mx, my)
        else:
            self._render_horizontal(gc, lx, ly, rx, ry, mx, my)

    def _render_vertical(self, gc, lx, ly, rx, ry, mx, my):
        """     M       L _____ R
                |           |
             L__|__R  or    |
                            M

        """
        mx = lx + (rx - lx) / 2.
        with gc:
            gc.set_line_width(20)
            gc.set_stroke_color(self._get_border_color())
            tee_v(gc, lx, ly, rx, mx, my)

        gc.set_line_width(10)
        self.set_fill_color(gc)
        tee_v(gc, lx, ly, rx, mx, my)

    def _render_horizontal(self, gc, lx, ly, rx, ry, mx, my):
        """
        L             R
        |____ M  M____|
        |             |
        R             L
        """

        with gc:
            gc.set_line_width(20)
            gc.set_stroke_color(self._get_border_color())
            tee_h(gc, lx, ly, mx, my, ry)

        gc.set_line_width(10)
        self.set_fill_color(gc)
        tee_h(gc, lx, ly, mx, my, ry)


def elbow(gc, sx, sy, ex, ey, corner='ul'):
    x1 = sx
    y1 = sy
    x3 = ex
    y3 = ey
    if corner == 'ul':
        x2 = sx
        y2 = ey
    elif corner == 'lr':
        x2 = ex
        y2 = sy
    elif corner == 'll':
        x2 = ex
        y2 = sy
    else:
        x2 = sx
        y2 = ey

    # draw border
    gc.move_to(x1, y1)
    gc.line_to(x2, y2)
    gc.line_to(x3, y3)
    gc.stroke_path()


class Elbow(BorderLine):
    corner = 'ul'

    def _render_(self, gc):
        sx, sy = self.start_point.get_xy()
        ex, ey = self.end_point.get_xy()
        with gc:
            gc.set_line_width(20)
            gc.set_stroke_color(self._get_border_color())

            elbow(gc, sx, sy, ex, ey, self.corner)
        gc.set_line_width(10)
        self.set_fill_color(gc)
        elbow(gc, sx, sy, ex, ey, self.corner)

# ============= EOF =============================================



