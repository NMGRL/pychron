# ===============================================================================
# Copyright 2012 Jake Ross
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
import os

from traits.api import Dict

# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.base_scene_loader import floatify, colorify
from pychron.canvas.canvas2D.scene.primitives.lasers import Laser, CircleLaser
from pychron.canvas.canvas2D.scene.primitives.primitives import Label, BorderLine, Image, ValueLabel
from pychron.canvas.canvas2D.scene.primitives.pumps import Turbo, IonPump
from pychron.canvas.canvas2D.scene.primitives.rounded import CircleStage, Spectrometer, Getter
from pychron.canvas.canvas2D.scene.primitives.valves import RoughValve, Valve
from pychron.canvas.canvas2D.scene.scene import Scene
from pychron.canvas.canvas2D.scene.xml_scene_loader import XMLLoader
from pychron.canvas.canvas2D.scene.yaml_scene_loader import YAMLLoader


class ExtractionLineScene(Scene):
    valves = Dict
    rects = Dict
    widgets = Dict

    def load(self, pathname, configpath, valvepath, canvas):
        self.overlays = []
        self.reset_layers()
        origin, color_dict, valve_dimension, images = self._load_config(configpath, canvas)
        if pathname.endswith('.yaml') or pathname.endswith('.yml'):
            klass = YAMLLoader
        else:
            klass = XMLLoader

        loader = klass(pathname, origin, color_dict, valve_dimension)

        loader.load_switchables(self, valvepath)
        loader.load_rects(self)
        loader.load_pipettes(self)
        loader.load_markup(self)
        loader.load_widgets(self, canvas)
        #
        # # need to load all components that will be connected
        # # before loading connections
        #
        loader.load_connections(self)
        loader.load_legend(self)
        loader.load_config_images(self, images)

    def get_is_in(self, px, py, exclude=None):
        if exclude is None:
            exclude = [Valve, RoughValve, Image, Label,
                       ValueLabel,
                       BorderLine, ]

        for c in self.iteritems(exclude=exclude):
            # x, y = c.get_xy()
            # w, h = c.get_wh()
            if c.identifier in ('bounds_rect', 'legend'):
                continue

            if c.is_in(px, py):
                return c
                # if x <= px <= x + w and y <= py <= y + h:
                # return c

    def _load_config(self, p, canvas):
        color_dict = dict()
        ox, oy = 0, 0
        valve_dimension = 2, 2
        images = []
        if os.path.isfile(p):
            cp = self._get_canvas_parser(p)
            tree = cp.get_tree()
            if tree:
                images = cp.get_elements('image')
                xv, yv = self._get_canvas_view_range(cp)

                canvas.view_x_range = xv
                canvas.view_y_range = yv
                dim = tree.find('valve_dimension')
                valve_dimension = 2, 2
                if dim is not None:
                    valve_dimension = floatify(dim)

                # get label font
                font = tree.find('font')
                if font is not None:
                    self.font = font.text.strip()

                # get default colors
                for c in tree.findall('color'):
                    k = c.get('tag')

                    color = colorify(c)
                    if k == 'bgcolor':
                        if ',' in color:
                            color = [i / 255. for i in floatify(color)]
                        # if isinstance(color, list):
                        #     color = [ti / 255. for ti in color]
                        canvas.bgcolor = color
                    else:
                        color_dict[k] = color

                # get an origin offset

                o = tree.find('origin')
                if o is not None:
                    ox, oy = floatify(o)

        return (ox, oy), color_dict, valve_dimension, images

# ============= EOF =============================================
