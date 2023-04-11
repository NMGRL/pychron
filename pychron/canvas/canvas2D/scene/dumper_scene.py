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
from __future__ import absolute_import
from pychron.canvas.canvas2D.scene.extraction_line_scene import ExtractionLineScene
from pychron.canvas.canvas2D.scene.primitives.dumper_primitives import Gate, Funnel
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle
from pychron.canvas.canvas2D.scene.xml_scene_loader import XMLLoader
from pychron.canvas.canvas2D.scene.yaml_scene_loader import YAMLLoader

KLASS_MAP = {"gate": Gate, "funnel": Funnel}


class DumperScene(ExtractionLineScene):
    def load(self, pathname, configpath, valvepath, canvas):
        self.overlays = []
        self.reset_layers()

        (
            origin,
            color_dict,
            valve_dimension,
            _,
            connection_dimension,
        ) = self._load_config(configpath, canvas)
        if pathname.endswith(".yaml") or pathname.endswith(".yml"):
            klass = YAMLLoader
        else:
            klass = XMLLoader

        loader = klass(
            pathname, origin, color_dict, valve_dimension, connection_dimension
        )

        loader.load_switchables(self, valvepath)
        loader.load_rects(self)
        loader.load_markup(self)
        loader.load_stateables(self)

    def _load_stateables(self, cp, origin, color_dict):
        for key in ("gate", "funnel"):
            for b in cp.get_elements(key):
                if key in color_dict:
                    c = color_dict[key]
                else:
                    c = (204, 204, 204)

                klass = KLASS_MAP.get(key, RoundedRectangle)
                rect = self._new_rectangle(
                    cp, b, c, bw=5, origin=origin, klass=klass, type_tag=key
                )
                self._load_states(rect, b)

    def _load_states(self, item, elem):
        closed_state = {
            "translation": (item.x, item.y),
            "dimension": (item.width, item.height),
        }
        states = {"closed": closed_state}
        for state in elem.findall("state"):
            try:
                trans = self._get_floats(state, "translation")
            except:
                trans = item.x, item.y
            try:
                dim = self._get_floats(state, "dimension")
            except:
                dim = item.width, item.height

            d = {"translation": trans, "dimension": dim}

            states[state.text.strip()] = d

        item.states = states


# ============= EOF =============================================
