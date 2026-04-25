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
import math
import os

from pychron.canvas.canvas2D.scene.primitives.primitives import Image
from pychron.canvas.canvas2D.scene.primitives.rounded import (
    RoundedRectangle,
    CircleStage,
)
from pychron.paths import icons, paths


class CircleLaser(CircleStage):
    pass


class Laser(RoundedRectangle):
    cnt_tol = 5
    radius = 4
    use_symbol = True

    def __init__(self, x, y, *args, **kw):
        super(Laser, self).__init__(x, y, *args, **kw)
        # path = os.path.join(icons, 'laser.png')
        # self._img = Image(x, y, path=path, scale=(0.05, 0.05))

    # def set_canvas(self, canvas):
    #     super(Laser, self).set_canvas(canvas)
    # self._img.set_canvas(canvas)

    def toyaml(self):
        yd = super(Laser, self).toyaml()
        yd["use_symbol"] = self.use_symbol
        return yd

    def _get_name_xy(self, x, y, w, h):
        return x, y + (0.25 * h)

    def _render(self, gc):
        super(Laser, self)._render(gc)
        if self.use_symbol:
            x, y = self.get_xy()
            with gc:
                gc.set_fill_color(self._convert_color((250, 243, 13)))
                gc.set_stroke_color((0, 0, 0))
                gc.set_line_width(2)
                gc.translate_ctm(x, y)
                ww, hh = self.get_wh()
                # w = w / 2
                # h = w
                w = 40
                h = 32
                gc.translate_ctm((ww - w) / 2.0, hh / 8)
                with gc:
                    gc.set_line_width(3)
                    gc.move_to(0, 0)
                    gc.line_to(w, 0)
                    gc.line_to(w / 2, h)
                    gc.line_to(0, 0)
                    gc.draw_path()
                    gc.stroke_path()

                gc.set_fill_color((0, 0, 0))
                # gc.arc(w/2, 10, 3, 0, 360)
                # gc.draw_path()

                gc.translate_ctm(w / 2, 12)
                gc.move_to(0, 0)
                gc.line_to(14, 0)
                gc.stroke_path()

                n = 8
                step = 360 / n
                for i in range(n):
                    with gc:
                        gc.rotate_ctm(math.radians(i * step))
                        gc.move_to(0, 0)
                        gc.line_to(8, 0)
                        gc.stroke_path()

    #     iw = 60
    #     gc.translate_ctm((w - iw) / 2, 0)
    #     self._img.render(gc)
    #
    #     if self.animate:
    #         self._draw_firing(gc)
    #
    # def _draw_firing(self, gc):
    #     """
    #     draw an led stream
    #
    #     0 X X X X X
    #     X 0 X X X X
    #     X X 0 X X X
    #     X X X 0 X X
    #     X X X X 0 X
    #     X X X X X 0
    #     0 X X X X X
    #
    #     :param gc:
    #     :return:
    #     """
    #     nleds = self.cnt_tol
    #     x, y = self.get_xy()
    #     gc.translate_ctm(x, y)
    #     radius = self.radius
    #     diam = radius * 2
    #     for i in range(nleds):
    #         gc.translate_ctm(0, -diam - 1)
    #         with gc:
    #             if i == self.cnt:
    #                 color = (1, 0, 0, 1)
    #             else:
    #                 color = (1, 0.65, 0, 0.6)
    #
    #             gc.set_fill_color(color)
    #             gc.set_stroke_color(color)
    #
    #             gc.arc(0, 0, radius, 0, 360)
    #             gc.draw_path()
    #
    #     self.increment_cnt()


# ============= EOF =============================================
