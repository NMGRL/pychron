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
from traits.api import Str, Enum, Float
from traitsui.api import View, Item, HGroup, Label, UItem

from pychron.canvas.canvas2D.scene.primitives.base import QPrimitive
from pychron.canvas.canvas2D.scene.primitives.primitives import (
    Point,
    Bordered,
    BorderLine,
)
from pychron.pychron_constants import NULL_STR


class ConnectionMixin:
    orientation = Enum(NULL_STR, "vertical", "horizontal")
    start = Str
    end = Str
    start_offsetx = Float
    start_offsety = Float

    end_offsetx = Float
    end_offsety = Float

    @property
    def end_offset(self):
        return "{:0.2f},{:0.2f}".format(self.end_offsetx, self.end_offsety)

    @property
    def start_offset(self):
        return "{:0.2f},{:0.2f}".format(self.start_offsetx, self.start_offsety)

    def edit_view(self):
        v = View(
            Item("orientation"),
            HGroup(
                Item("start"),
                Label("Offset"),
                UItem("start_offsetx"),
                UItem("start_offsety"),
            ),
            HGroup(
                Item("end"), Label("Offset"), UItem("end_offsetx"), UItem("end_offsety")
            ),
        )
        return v


class Connection(ConnectionMixin, BorderLine):
    tag = "connection"
    width = 10

    def toyaml(self):
        y = super(Connection, self).toyaml()
        del y["dimension"]
        del y["translation"]
        del y["name"]

        y["start"] = {"name": str(self.start), "offset": str(self.start_offset)}
        y["end"] = {"name": str(self.end), "offset": str(self.end_offset)}
        return y


class RConnection(Connection):
    tag = "rconnection"
    border_width = 6
    width = 3

    # def _render_augmented_border(self, gc):
    #     bc = self._get_border_color()
    #     x, y = self.start_point.get_xy()
    #     x1, y1 = self.end_point.get_xy()
    #
    #     i = 0
    #     step = 10
    #     if y1 < y or x1 < x:
    #         step = -10
    #
    #     while 1:
    #         gc.set_line_width(0)
    #         gc.set_fill_color(bc)
    #         # step = 10
    #         with gc:
    #             if x1 == x:
    #                 cx = self.width+1
    #                 cy = 0
    #                 tx = x
    #                 ty = y + (step * i)
    #             else:
    #                 cx = 0
    #                 cy = self.width+1
    #                 tx = x + (step * i)
    #                 ty = y
    #
    #             gc.translate_ctm(tx, ty)
    #             gc.arc(-cx, -cy, 4, 0, 360)
    #             gc.arc(cx, cy, 4, 0, 360)
    #             gc.draw_path()
    #
    #         i += 1
    #         if x1 == x and (ty > max(y1, y) or ty < min(y1, y)):
    #             break
    #         elif tx > max(x1, x) or tx < min(x1, x):
    #             break

    def _render(self, gc):
        # bc = self._get_border_color()
        # with gc:
        #     # w, h = self.get_wh()
        #     gc.set_line_width(self.width + 10)
        #
        #     gc.set_stroke_color(bc)
        #
        #     x, y = self.start_point.get_xy()
        #     x1, y1 = self.end_point.get_xy()
        #     # draw border
        #     gc.move_to(x, y)
        #     gc.line_to(x1, y1)
        #     gc.draw_path()

        super(RConnection, self)._render(gc)

        # draw border vertical augmentation
        self._render_augmented_border(gc)
        # with gc:
        #     gc.set_line_width(self.width+4)
        #
        #     gc.set_stroke_color(self._convert_color(self.inner_border_color))
        #
        #     x, y = self.start_point.get_xy()
        #     x1, y1 = self.end_point.get_xy()
        #     # draw border
        #     gc.move_to(x, y)
        #     gc.line_to(x1, y1)
        #     gc.draw_path()


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


class Fork(ConnectionMixin, QPrimitive, Bordered):
    tag = "fork"
    left = None
    right = None
    mid = None
    height = 10
    inverted = False
    border_width = 10

    def set_midpoint(self, p1, **kw):
        if isinstance(p1, tuple):
            p1 = Point(*p1, **kw)
        self.mid = p1

    def set_leftpoint(self, p1, **kw):
        if isinstance(p1, tuple):
            p1 = Point(*p1, **kw)
        self.left = p1

    def set_rightpoint(self, p1, **kw):
        if isinstance(p1, tuple):
            p1 = Point(*p1, **kw)
        self.right = p1

    def get_midx(self):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        return lx + (rx - lx) / 2.0

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

    def _render(self, gc):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        mx, my = self.mid.get_xy()
        # ly, ry = ly - 30, ry - 30
        mx = lx + (rx - lx) / 2.0

        w, h = self.get_wh()
        # print self.height, h, self.canvas
        # M
        # |
        # _|_
        # |   |
        # L   R
        with gc:
            gc.set_line_width(self.width + self.border_width)
            gc.set_stroke_color(self._get_border_color())

            # gc.set_line_width(5)
            # fill in corners
            gc.move_to(lx - 10, ly + h - 5)
            gc.line_to(rx + 10, ly + h - 5)

            fork(gc, lx, ly, rx, ry, mx, my, h)

        gc.set_line_width(self.width + self.border_width)
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


class Cross(ConnectionMixin, QPrimitive, Bordered):
    tag = "cross"
    left = None
    right = None
    top = None
    bottom = None
    height = 10
    border_width = 10

    def render_border_gaps(self, gc, t, x, y, cx, cy, width, height, cw4):
        if t == "left":
            xx, yy = self.left.get_xy()
            x1 = xx
            x2 = xx
            y1 = yy - cw4
            y2 = yy + cw4
        elif t == "right":
            xx, yy = self.right.get_xy()
            xx -= width / 2
            x1 = xx
            x2 = xx
            y1 = yy - cw4
            y2 = yy + cw4
        elif t == "top":
            xx, yy = self.top.get_xy()
            yy -= height / 2
            x1 = xx - cw4
            x2 = xx + cw4
            y1 = yy
            y2 = yy
        else:  # t == bottom
            xx, yy = self.bottom.get_xy()
            yy += height / 2
            x1 = xx - cw4
            x2 = xx + cw4
            y1 = yy
            y2 = yy

        gc.move_to(x1, y1)
        gc.line_to(x2, y2)

    def set_points(self, lx, ly, rx, ry, tx, ty, bx, by):
        self.left = Point(lx, ly)
        self.right = Point(rx, ry)
        self.top = Point(tx, ty)
        self.bottom = Point(bx, by)

    def set_canvas(self, canvas):
        self.left.set_canvas(canvas)
        self.right.set_canvas(canvas)
        self.top.set_canvas(canvas)
        self.bottom.set_canvas(canvas)
        super(Cross, self).set_canvas(canvas)

    def _render(self, gc):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        tx, ty = self.top.get_xy()
        bx, by = self.bottom.get_xy()

        # ly, ry = ly - 30, ry - 30

        # w, h = self.get_wh()

        with gc:
            gc.set_line_width(self.width + self.border_width)
            gc.set_stroke_color(self._get_border_color())

            # gc.set_line_width(5)
            # fill in corners
            # gc.move_to(lx - 10, ly + h - 5)
            # gc.line_to(rx + 10, ly + h - 5)

            cross(gc, lx, ly, rx, ry, tx, ty, bx, by)

        gc.set_line_width(self.width)
        self.set_fill_color(gc)
        cross(gc, lx, ly, rx, ry, tx, ty, bx, by)


def cross(gc, lx, ly, rx, ry, tx, ty, bx, by):
    # draw main horizontal
    gc.move_to(lx, ly)
    gc.line_to(rx, ly)

    # draw main vertical
    gc.move_to(tx, ty)
    gc.line_to(bx, by)

    gc.draw_path()


class Tee(Fork):
    tag = "tee"

    def render_border_gaps(self, gc, t, x, y, cx, cy, width, height, cw4):
        if t == "mid":
            # tee is vertical
            if self.is_vertical:
                # mx = c.get_midx()
                mx = self.mid.get_xy()[0]
                yy = y if self.left.y < cy else y + height
                gc.move_to(mx - cw4, yy)
                gc.line_to(mx + cw4, yy)

            else:
                xx = x if self.left.x < cx else x + width
                # xx = c.mid.get_xy()[0]
                yy = y + height / 2

                gc.move_to(xx, yy - cw4)
                gc.line_to(xx, yy + cw4)
        elif t == "left":
            xx, yy = self.left.get_xy()
            if self.is_vertical:
                xx += width / 2
                x1 = x2 = xx
                y1 = yy - cw4
                y2 = yy + cw4

            else:
                x1 = x2 = xx
                x1 -= cw4
                x2 += cw4
                if self.left.y < self.right.y:
                    yy = y + height
                else:
                    yy = y
                y1 = y2 = yy

            gc.move_to(x1, y1)
            gc.line_to(x2, y2)
        elif t == "right":
            xx, _ = self.right.get_xy()

            if self.is_vertical:
                xx -= width / 2
                _, yy = self.left.get_xy()
                x1 = x2 = xx
                y1 = yy - cw4
                y2 = yy + cw4

            else:
                xx = self.right.get_xy()[0]
                if self.left.y > self.right.y:
                    yy = y + height
                else:
                    yy = y
                xx += self.border_width
                x1 = xx - cw4
                x2 = xx + cw4
                y1 = y2 = yy

            gc.move_to(x1, y1)
            gc.line_to(x2, y2)

    def _render(self, gc):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        mx, my = self.mid.get_xy()
        # ly, ry = ly - 30, ry - 30
        if self.is_vertical:
            self._render_vertical(gc, lx, ly, rx, ry, mx, my)
        else:
            self._render_horizontal(gc, lx, ly, rx, ry, mx, my)

    @property
    def is_vertical(self):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        mx, my = self.mid.get_xy()
        return ly == ry or (my < ly and my < ry) or (my > ly and my > ry)

    def _render_vertical(self, gc, lx, ly, rx, ry, mx, my):
        """M       L _____ R
           |           |
        L__|__R  or    |
                       M

        """
        with gc:
            gc.set_line_width(self.width + self.border_width)
            gc.set_stroke_color(self._get_border_color())
            tee_v(gc, lx, ly, rx, mx, my)

        gc.set_line_width(self.width)
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
            gc.set_line_width(self.border_width + self.width)
            gc.set_stroke_color(self._get_border_color())
            tee_h(gc, lx, ly, mx, my, ry)

        gc.set_line_width(self.width)
        self.set_fill_color(gc)
        tee_h(gc, lx, ly, mx, my, ry)


def elbow(gc, sx, sy, ex, ey, corner="ul"):
    x1 = sx
    y1 = sy
    x3 = ex
    y3 = ey
    if corner == "ul":
        x2 = sx
        y2 = ey
    elif corner == "lr":
        x2 = ex
        y2 = sy
    elif corner == "ll":
        x2 = sx
        y2 = ey
    else:
        x2 = sx
        y2 = ey

    # draw border
    gc.move_to(x1, y1)
    gc.line_to(x2, y2)
    gc.line_to(x3, y3)
    gc.stroke_path()


class Elbow(ConnectionMixin, BorderLine):
    corner = "ul"
    tag = "elbow"

    def render_border_gaps(self, gc, t, x, y, cx, cy, width, height, cw4):
        p1, p2 = self.start_point, self.end_point

        if p1.y < p2.y:
            p1x, p1y = p1.get_xy()
            x1 = p1x - cw4
            x2 = p1x + cw4
            y1 = y2 = y + height
            # gc.move_to(p1x - cw4, y + height)
            # gc.line_to(p1x + cw4, y + height)
        else:
            if self.corner == "ll":
                p1x, p1y = p1.get_xy()
                x1 = p1x - cw4
                x2 = p1x + cw4
                y1 = y2 = p1y
                # gc.move_to(p1x - 5, p1y)
                # gc.line_to(p1x + 5, p1y)
            else:
                p2x, p2y = p2.get_xy()
                xx = x

                if p1.x >= cx:
                    xx = x + width

                x1 = x2 = xx
                y1 = p2y - cw4
                y2 = p2y + cw4

                # gc.move_to(xx, p2y - cw4)
                # gc.line_to(xx, p2y + cw4)

        gc.move_to(x1, y1)
        gc.line_to(x2, y2)

    def _render(self, gc):
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
