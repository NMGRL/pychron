# ===============================================================================
# Copyright 2013 Jake Ross
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

from numpy import Inf
# ============= enthought library imports =======================
from traits.api import Int

from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.scene import Scene


# ============= standard library imports ========================


class LoadingScene(Scene):
    nholes = Int

    def load(self, holes, show_hole_numbers=True):
        self.reset_layers()
        self._load_holes(holes, show_hole_numbers)

    def _load_holes(self, holes, show_hole_numbers=False):
        xmi, ymi, xma, yma, mr = Inf, Inf, -Inf, -Inf, -Inf
        self.nholes = len(holes)
        for x, y, r, n in holes:
            r *= 0.5
            xmi, xma = min(xmi, x), max(xma, x)
            ymi, yma = min(ymi, y), max(yma, y)

            mr = max(mr, r)
            v = LoadIndicator(x=x,
                              y=y,
                              radius=r,
                              name_visible=show_hole_numbers,
                              name=n,
                              font='modern 10')
            self.add_item(v)

        xd = (xma - xmi) / 2. + xmi
        yd = (yma - ymi) / 2. + ymi
        w = (xma + mr - (xmi - mr)) * 1.2
        h = (yma + mr - (ymi - mr)) * 1.2
        w /= 2.0
        h /= 2.0
        self._xrange = -w + xd, w + xd
        self._yrange = -h + yd, h + yd

# ============= EOF =============================================
