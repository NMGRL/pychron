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
from pychron.canvas.canvas2D.scene.primitives.primitives import QPrimitive, Point, Bordered
def fork(gc, lx, ly, rx, ry, mx, my, h):
    # draw left prong
    gc.move_to(lx,ly)
    gc.line_to(lx, ly+h)

    # draw right prong
    gc.move_to(rx,ry)
    gc.line_to(rx, ry+h)

    # draw connector
    gc.move_to(lx-5, ly+h-5)
    gc.line_to(rx+5, ly+h-5)

    # draw handle
    gc.move_to(mx, ly+h)
    gc.line_to(mx, my)
    gc.draw_path()


class Fork(QPrimitive, Bordered):
    left = None
    right = None
    mid = None
    height = 10
    inverted=False
    def set_points(self, lx, ly, rx, ry, mx, my):
        self.left = Point(lx, ly)
        self.right = Point(rx, ry)
        self.mid = Point(mx, my)

        self.inverted = my>ly

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

        w,h = self.get_wh()
        # print self.height, h, self.canvas
        #   M
        #   |
        #  _|_
        # |   |
        # L   R
        with gc:
            gc.set_line_width(20)
            gc.set_stroke_color(self._get_border_color())

            # gc.set_line_width(5)
            # fill in corners
            gc.move_to(lx-10, ly+h-5)
            gc.line_to(rx+10, ly+h-5)

            fork(gc, lx, ly, rx, ry, mx, my, h)

        gc.set_line_width(10)
        # self.set_fill_color(gc)
        fork(gc, lx, ly, rx, ry, mx, my, h)


class Tee(Fork):
    def _render_(self, gc):
        lx, ly = self.left.get_xy()
        rx, ry = self.right.get_xy()
        mx, my = self.mid.get_xy()
        # ly, ry = ly - 30, ry - 30
        mx = lx + (rx - lx) / 2.
        with gc:
            if not self.inverted:
                # draw main border
                gc.set_line_width(5)
                gc.set_stroke_color(self._get_border_color())
                gc.move_to(lx, ly + 7)
                gc.line_to(rx, ly + 7)

                gc.move_to(lx, ly - 7)
                gc.line_to(rx, ly - 7)

                gc.move_to(mx-7, ly-7)
                gc.line_to(mx-7, my)
                gc.move_to(mx+7, ly-7)
                gc.line_to(mx+7, my)
                gc.draw_path()

        gc.set_line_width(10)
        self.set_fill_color(gc)
        # gc.set_stroke_color(self._convert_color(self.default_color))

        # draw main horizontal
        gc.move_to(lx, ly)
        gc.line_to(rx, ry)
        # draw vertical
        gc.move_to(mx, ly)
        gc.line_to(mx, my)
        gc.draw_path()




# ============= EOF =============================================



