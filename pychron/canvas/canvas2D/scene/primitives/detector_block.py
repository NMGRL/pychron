# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Float
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.primitives import Rectangle


class Detector(Rectangle):
    deflection = Float

    min_deflection = Float(0)
    max_deflection = Float(100)

    def _render(self, gc):
        x, y = self.get_xy(clear_layout_needed=False)
        w, h = self.get_wh()

        # render deflectors
        with gc:
            gc.rect(x - 25, y, 20, 2)
            gc.rect(x - 25, y + h - 2, 20, 2)
            gc.draw_path()

        # render nominal center line
        with gc:
            cx, cy = self._cached_xy
            cy -= self.offset_y
            gc.set_stroke_color((0, 0, 0))
            gc.set_line_dash([5, 5])
            gc.move_to(cx - 150, cy + h / 2.)
            gc.line_to(cx + 50, cy + h / 2.)
            gc.stroke_path()

        # render deflected beam
        with gc:
            gc.set_line_width(3)
            gc.set_stroke_color((0, 1, 0))
            m = y + h / 2.
            y2 = m + h / 2. * self.deflection / (
                self.max_deflection - self.min_deflection)
            gc.move_to(x - 25, m)
            gc.line_to(x, y2)
            gc.stroke_path()

        super(Detector, self)._render(gc)

# ============= EOF =============================================
