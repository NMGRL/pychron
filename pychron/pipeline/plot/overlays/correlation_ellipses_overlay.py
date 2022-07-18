# ===============================================================================
# Copyright 2020 ross
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
from chaco.abstract_overlay import AbstractOverlay
from numpy import linspace, sqrt, hstack, column_stack


class CorrelationEllipsesOverlay(AbstractOverlay):
    fill = False

    def __init__(self, correlation_ellipses, colors, *args, **kw):
        self.correlation_ellipses = correlation_ellipses
        self.colors = colors
        super(CorrelationEllipsesOverlay, self).__init__(*args, **kw)

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        for ((k, ci), color) in zip(self.correlation_ellipses, self.colors):
            with gc:
                age = ci["age"]
                kca = ci["kca"]

                a = age["max"] - age["min"]
                b = kca["max"] - kca["min"]
                cx = a / 2.0 + age["min"]
                cy = b / 2.0 + kca["min"]

                (cx, cy), (a, oy), (ox, b) = other_component.map_screen(
                    [(cx, cy), (a, 0), (0, b)]
                )

                w, h = a - ox, b - oy
                a, b = w / 2.0, h / 2.0

                x1 = linspace(-a, a, 200)
                y1 = b * sqrt((1 - (x1 / a) ** 2))

                x2 = x1[::-1]
                y2 = -b * sqrt((1 - (x2 / a) ** 2))

                x = hstack((x1, x2))
                y = hstack((y1, y2))
                pts = column_stack((x, y))

                gc.translate_ctm(cx, cy)
                gc.begin_path()
                gc.lines(pts)

                color = (color.redF(), color.greenF(), color.blueF())
                gc.set_stroke_color(color)
                gc.stroke_path()

                gc.set_fill_color(color)
                gc.set_text_position(0, b + 3)
                gc.show_text(k)

        # if self.fill:
        #     c = self.border_color_
        #     c = c[0], c[1], c[2], 0.5
        #     gc.set_fill_color(c)
        #     gc.draw_path()
        # else:
        #     gc.stroke_path()


# ============= EOF =============================================
