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
# ============= standard library imports ========================
# ============= local library imports  ==========================


# ============= EOF =============================================
from pychron.canvas.canvas2D.scene.primitives.primitives import Rectangle


class Detector(Rectangle):
    def _render(self, gc):
        x, y = self.get_xy(clear_layout_needed=False)
        w, h = self.get_wh()

        # render deflectors
        with gc:
            gc.rect(x - 25, y, 20, 2)
            gc.rect(x - 25, y + h - 2, 20, 2)
            gc.draw_path()

        with gc:
            x, y = self._cached_xy
            y -= self.offset_y
            gc.set_stroke_color((0, 0, 0))
            gc.set_line_dash([5, 5])
            gc.move_to(x - 150, y + h / 2.)
            gc.line_to(x + 50, y + h / 2.)
            gc.stroke_path()

        super(Detector, self)._render(gc)
