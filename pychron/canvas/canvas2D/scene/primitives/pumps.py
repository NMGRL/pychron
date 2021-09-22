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
import math
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.primitives import Animation
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle, rounded_rect


class IonPump(RoundedRectangle):
    pass


class Turbo(RoundedRectangle):
    use_symbol = False

    def _render(self, gc):
        corner_radius = self.corner_radius
        with gc:
            width, height = self.get_wh()
            x, y = self.get_xy()
            if self.fill:
                rounded_rect(gc, x, y, width, height, corner_radius)

            self._render_border(gc, x, y, width, height)
            # h = height
            if self.use_symbol:
                w = width * 0.75
                h = w
                xx = x + (width - w) / 2
                yy = y - h
                rounded_rect(gc, xx, yy, w, h, corner_radius)
                self._render_border(gc, xx, yy, w, h, use_border_gaps=False)
                self._draw_impeller(gc, xx, yy, w, h)

            gc.set_fill_color(self._convert_color(self.name_color))
            if self.display_name:
                self._render_textbox(gc, x, y, width, height,
                                     self.display_name)
            elif not self.display_name == '':
                self._render_name(gc, x, y, width, height)

        # super(Turbo, self)._render(gc)
        # if self.animate:
        #     self._draw_impeller(gc)

    def _draw_impeller(self, gc, x, y, w, h):
        with gc:
            # x, y = self.get_xy(clear_layout_needed=False)
            # w, h = self.get_wh()
            # c = self._convert_color(self.default_color)
            c = self._get_border_color()
            gc.set_fill_color(c)

            cx = x + w / 2.
            cy = y + h / 2.
            gc.translate_ctm(cx, cy)

            # gc.set_fill_color((0, 0, 0))

            l = 20
            w = 6
            # gc.rotate_ctm(math.radians(self.cnt))
            n = 6.
            step = 360 / n
            for i in range(int(n)):
                with gc:
                    gc.rotate_ctm(math.radians(i * step))
                    gc.move_to(0, 0)
                    gc.line_to(l, -w)
                    gc.line_to(l, w)
                    gc.line_to(0, 0)
                    gc.draw_path()
                    gc.stroke_path()

            gc.arc(0, 0, 7, 0, 360)
            gc.draw_path()
        # self.increment_cnt(15)
        # if self.refresh_required():

# ============= EOF =============================================
