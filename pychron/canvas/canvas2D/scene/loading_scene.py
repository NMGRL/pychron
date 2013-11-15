#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
import os

from numpy import Inf

#============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.scene import Scene
from pychron.paths import paths
from pychron.lasers.stage_managers.stage_map import StageMap
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator


class LoadingScene(Scene):
    def load(self, t, show_hole_numbers=True):
        self.reset_layers()
        holes = self._get_holes(t)

        self._load_holes(holes, show_hole_numbers)

    def _get_holes(self, t):
        p = os.path.join(paths.map_dir, t)
        sm = StageMap(file_path=p)

        holes = ((hi.x, hi.y, hi.dimension / 2.0, hi.id) for hi in sm.sample_holes)
        return holes

    def _load_holes(self, holes, show_hole_numbers=False):
        xmi, ymi, xma, yma, mr = Inf, Inf, -Inf, -Inf, -Inf
        for x, y, r, n, in holes:
            xmi = min(xmi, x)
            ymi = min(ymi, y)
            xma = max(xma, x)
            yma = max(yma, y)
            mr = max(mr, r)
            v = LoadIndicator(
                x=x,
                y=y,
                radius=r,
                name_visible=show_hole_numbers,
                name=n,
                font='modern 10'
            )
            self.add_item(v)

        w = (xma + mr - (xmi - mr)) * 1.2
        h = (yma + mr - (ymi - mr)) * 1.2
        w /= 2.0
        h /= 2.0
        self._xrange = -w, w
        self._yrange = -h, h


#============= EOF =============================================
