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
from pychron.canvas.canvas2D.scene.primitives.rounded import (
    RoundedRectangle,
    rounded_rect,
)


class Pump(RoundedRectangle):
    use_symbol = False

    def toyaml(self):
        d = super(Pump, self).toyaml()
        d["use_symbol"] = self.use_symbol
        return d

    def _render_base_symbol(self, gc, br):
        gc.arc(0, 0, br, 0, 360)

        for a, b in ((60, -30), (120, -150)):
            a = math.radians(a)
            b = math.radians(b)
            xx = br * math.cos(a)
            yy = br * math.sin(a)
            gc.move_to(xx, yy)

            x2 = br * math.cos(b)
            y2 = br * math.sin(b)
            gc.line_to(x2, y2)
            gc.stroke_path()


class IonPump(Pump):
    def _render(self, gc):
        super(IonPump, self)._render(gc)
        if self.use_symbol:
            self._render_symbol(gc)

    def _render_symbol(self, gc):
        corner_radius = self.corner_radius
        width, height = self.get_wh()
        x, y = self.get_xy()
        w = width * 0.75
        h = w
        xx = x + (width - w) / 2
        yy = y - h
        with gc:
            rounded_rect(gc, xx, yy, w, h, corner_radius)
            self._render_border(gc, xx, yy, w, h, use_border_gaps=False)

        with gc:
            gc.set_line_width(2)
            gc.set_stroke_color((0.1, 0.1, 0.1))

            gc.translate_ctm(xx + w / 2, yy + h / 2)
            w2 = w / 2 - 15
            self._render_base_symbol(gc, w2 + 8)
            gc.rotate_ctm(math.radians(30))

            for i in range(3):
                with gc:
                    gc.rotate_ctm(math.radians(120 * i))
                    # with gc:
                    gc.move_to(0, 0)
                    gc.line_to(w2 - 2, 0)
                    gc.stroke_path()
                    gc.move_to(w2 - 6, 6)
                    gc.line_to(w2 - 2, 0)
                    gc.line_to(w2 - 6, -6)
                    gc.stroke_path()


class Turbo(Pump):
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
                self._render_symbol(gc, xx, yy, w, h)
                # self._draw_impeller(gc, xx, yy, w, h)

            gc.set_fill_color(self._convert_color(self.name_color))
            if self.display_name:
                self._render_textbox(gc, x, y, width, height, self.display_name)
            elif not self.display_name == "":
                self._render_name(gc, x, y, width, height)

        # super(Turbo, self)._render(gc)
        # if self.animate:
        #     self._draw_impeller(gc)

    def _render_symbol(self, gc, x, y, w, h):
        with gc:
            gc.set_line_width(2)
            gc.set_stroke_color((0.1, 0.1, 0.1))
            gc.translate_ctm(x + w / 2, y + h / 2)

            w2 = w / 2 - 15
            br = w2 + 8

            self._render_base_symbol(gc, br)

            gc.rotate_ctm(math.radians(30))
            gc.arc(0, 0, 4, 0, 360)
            gc.arc(0, 0, 8, 0, 360)
            gc.stroke_path()

    # def _draw_impeller(self, gc, x, y, w, h):
    #     with gc:
    #         # x, y = self.get_xy(clear_layout_needed=False)
    #         # w, h = self.get_wh()
    #         # c = self._convert_color(self.default_color)
    #         c = self._get_border_color()
    #         gc.set_fill_color(c)
    #
    #         cx = x + w / 2.
    #         cy = y + h / 2.
    #         gc.translate_ctm(cx, cy)
    #
    #         # gc.set_fill_color((0, 0, 0))
    #
    #         l = 20
    #         w = 6
    #         # gc.rotate_ctm(math.radians(self.cnt))
    #         n = 6.
    #         step = 360 / n
    #         for i in range(int(n)):
    #             with gc:
    #                 gc.rotate_ctm(math.radians(i * step))
    #                 gc.move_to(0, 0)
    #                 gc.line_to(l, -w)
    #                 gc.line_to(l, w)
    #                 gc.line_to(0, 0)
    #                 gc.draw_path()
    #                 gc.stroke_path()
    #
    #         gc.arc(0, 0, 7, 0, 360)
    #         gc.draw_path()
    # self.increment_cnt(15)
    # if self.refresh_required():


# ============= EOF =============================================
