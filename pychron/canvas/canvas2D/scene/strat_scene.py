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
import yaml

from pychron.canvas.canvas2D.scene.primitives.strat import StratItem
from pychron.canvas.canvas2D.scene.scene import Scene


class StratScene(Scene):
    def load(self, p):
        self.reset_layers()
        heights = []
        ages = []
        lowages = []
        highages = []
        # items=[]

        yd = self._get_dict(p)

        for yi in yd['items']:

            elev = yi['elevation']

            c = 0
            if elev in heights:
                c = heights.count(elev)

            age = yi['age']
            heights.append(elev)
            ages.append(age)
            err = yi['age_err']
            lowages.append(age - err * 2)
            highages.append(age + err * 2)
            v = StratItem(age,
                          elev,
                          error=err,
                          default_color=yi.get('color', 'black'),
                          soffset_x=c,
                          soffset_y=c * 12,
                          label_offsety=-15,
                          font='modern 10',
                          vjustify='center',
                          text=yi['label'],
                          use_border=False)
            self.add_item(v)

        self.value_limits = (min(heights), max(heights))
        self.index_limits = (min(lowages), max(highages))

    def _get_dict(self, p):
        if isinstance(p, (str, unicode)):
            with open(p, 'r') as rfile:
                p = yaml.load(rfile)

        return p

# ============= EOF =============================================

