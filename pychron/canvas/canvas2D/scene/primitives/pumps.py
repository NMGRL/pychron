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
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle


class Turbo(RoundedRectangle, Animation):
    animate = False

    def _render(self, gc):
        super(Turbo, self)._render(gc)
        if self.animate:
            self._draw_impeller(gc)

    def _draw_impeller(self, gc):
        with gc:
            x, y = self.get_xy(clear_layout_needed=False)
            w, h = self.get_wh()

            cx = x + w / 2.
            cy = y + h / 2. - 20
            gc.translate_ctm(cx, cy)

            gc.set_stroke_color((0, 0, 0))

            l = 10
            w = 3
            gc.rotate_ctm(math.radians(self.cnt))
            for i in (0, 1, 2):
                with gc:
                    gc.rotate_ctm(math.radians(i * 120))
                    gc.move_to(0, 0)
                    gc.line_to(l, -w)
                    gc.line_to(l, w)
                    gc.line_to(0, 0)
                    gc.stroke_path()

        self.increment_cnt(15)
        # if self.refresh_required():


# ============= EOF =============================================



