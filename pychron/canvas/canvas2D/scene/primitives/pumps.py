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
import time
import math
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.primitives import RoundedRectangle


class Animation(object):
    cnt = 0
    tol = 0.05
    _last_refresh = None

    def reset_cnt(self):
        self.cnt = 0

    def increment_cnt(self, inc=1):
        self.cnt += inc
        if self.cnt > 360:
            self.cnt -= 360

    def refresh_required(self):
        if not self._last_refresh or time.time() - self._last_refresh > self.tol:
            self._last_refresh = time.time()
            return True


class Turbo(RoundedRectangle, Animation):
    def _render_(self, gc):
        super(Turbo, self)._render_(gc)
        self._draw_impeller(gc)

    def _draw_impeller(self, gc):
        with gc:
            x, y = self.get_xy(clear_layout_needed=False)
            w, h = self.get_wh()

            cx = x + w / 2.
            cy = y + h / 2. - 20
            gc.translate_ctm(cx, cy)

            gc.set_stroke_color((0, 0, 0))
            # pw = 10
            # w2 = pw/2.
            # gc.rect(-w2,-w2,pw,pw)
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

        self.increment_cnt(10)
        # if self.refresh_required():

# ============= EOF =============================================



