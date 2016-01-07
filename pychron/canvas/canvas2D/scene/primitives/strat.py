# ===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
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
from pychron.canvas.canvas2D.scene.primitives.primitives import Label


class StratItem(Label):
    use_end_caps = True

    def _render(self, gc):
        self._render_label(gc)

        x, y = self.get_xy()

        gc.arc(x, y, 3, 0, 360)
        gc.fill_path()

        e = self.map_dimension(self.error)
        e1 = x - e * 2
        e2 = x + e * 2
        gc.move_to(e1, y)
        gc.line_to(e2, y)
        gc.stroke_path()
        if self.use_end_caps:
            startpts = [(e1, y - 5), (e2, y - 5)]
            endpts = [(e1, y + 5), (e2, y + 5)]
            gc.line_set(startpts, endpts)

            gc.stroke_path()

    def _render_label(self, gc):
        with gc:
            t = self.text
            x, y = self.get_xy()
            w, h, _, _ = gc.get_full_text_extent(t)

            x2 = x + w / 2.0
            x -= w / 2.0

            if x < self.canvas.x + 5:
                x = self.canvas.x + 5
            elif x2 > self.canvas.x2 - 5:
                x = self.canvas.x2 - w - 5

            gc.set_text_position(x, y + self.label_offsety)
            gc.show_text(t)

# ============= EOF =============================================

