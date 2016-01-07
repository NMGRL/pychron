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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.extraction_line_scene import ExtractionLineScene
from pychron.canvas.canvas2D.scene.primitives.dumper_primitives import Gate, Funnel
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle

KLASS_MAP = {'gate': Gate, 'funnel': Funnel}


class DumperScene(ExtractionLineScene):
    def load(self, pathname, configpath, valvepath, canvas):
        self.overlays = []
        self.reset_layers()

        cp = self._get_canvas_parser(pathname)
        origin, color_dict = self._load_config(configpath, canvas)

        self._load_switchables(cp, origin, valvepath)
        self._load_rects(cp, origin, color_dict)
        self._load_stateables(cp, origin, color_dict)
        self._load_markup(cp, origin, color_dict)

    def _load_stateables(self, cp, origin, color_dict):
        for key in ('gate', 'funnel'):
            for b in cp.get_elements(key):
                if key in color_dict:
                    c = color_dict[key]
                else:
                    c = (204, 204, 204)

                klass = KLASS_MAP.get(key, RoundedRectangle)
                rect = self._new_rectangle(b, c, bw=5, origin=origin, klass=klass, type_tag=key)
                self._load_states(rect, b)

    def _load_states(self, item, elem):
        closed_state = {'translation': (item.x, item.y), 'dimension': (item.width, item.height)}
        states = {'closed': closed_state}
        for state in elem.findall('state'):
            try:
                trans = self._get_floats(state, 'translation')
            except:
                trans = item.x, item.y
            try:
                dim = self._get_floats(state, 'dimension')
            except:
                dim = item.width, item.height

            d = {'translation': trans,
                 'dimension': dim}

            states[state.text.strip()] = d

        item.states = states

# ============= EOF =============================================
