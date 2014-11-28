# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
import yaml

from pychron.canvas.canvas2D.scene.scene import Scene

# from pychron.canvas.canvas2D.scene.primitives.primitives import Polygon, RasterPolygon
from pychron.canvas.canvas2D.scene.primitives.laser_primitives import RasterPolygon

#============= standard library imports ========================
#============= local library imports  ==========================

class LaserMineScene(Scene):
    def load(self, path):
        self.reset_layers()
        if path.endswith('.yaml'):
            self.load_yaml(path)
        else:
            pass

    def load_yaml(self, path):
        txt = open(path, 'r').read()
        yobj = yaml.load(txt)

        if 'polygons' in yobj:
            for k, po in yobj['polygons'].iteritems():
                self._new_polygon(po, k)

    def _new_polygon(self, po, key):
        pts = [pi['xy'] for pi in po['points']]
        item = RasterPolygon(pts, name=key, identifier=key)
        self.add_item(item)

    def _new_transect(self):
        pass





# ============= EOF =============================================
