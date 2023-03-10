# ===============================================================================
# Copyright 2021 ross
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
from pychron.canvas.canvas2D.scene.primitives.lasers import Laser, CircleLaser
from pychron.canvas.canvas2D.scene.primitives.primitives import Label
from pychron.canvas.canvas2D.scene.primitives.pumps import Turbo, IonPump
from pychron.canvas.canvas2D.scene.primitives.rounded import (
    CircleStage,
    Spectrometer,
    Getter,
    Stage,
    ColdFinger,
)
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle
from pychron.core.helpers.strtools import to_bool

KLASS_MAP = {
    "turbo": Turbo,
    "laser": Laser,
    "ionpump": IonPump,
    "getter": Getter,
    "coldfinger": ColdFinger,
    "spectrometer": Spectrometer,
    "circle_stage": CircleStage,
    "circle_laser": CircleLaser,
    "stage": Stage,
}

RECT_TAGS = (
    "stage",
    "laser",
    "spectrometer",
    "turbo",
    "getter",
    "tank",
    "ionpump",
    "gauge",
    "rectangle",
    "circle_stage",
    "circle_laser",
    "coldfinger",
)

SWITCH_TAGS = ("switch", "valve", "rough_valve", "manual_valve")


def get_offset(elem, default=None):
    offset = elem.get("offset")
    if default is None:
        default = 0, 0

    txt = ""
    if offset:
        txt = offset
        x, y = floatify(offset)
    else:
        x, y = default
    return x, y, txt


def floatify(a, delim=","):
    if not isinstance(a, str):
        a = a.text.strip()

    return [float(i) for i in a.split(delim)]


def colorify(a):
    if not isinstance(a, str):
        a = a.text.strip()

    if a.startswith("0x"):
        a = int(a, 16)
    return a


def make_color(c):
    if not isinstance(c, str):
        c = ",".join(map(str, list(map(int, c))))
        c = "({})".format(c)
    return c


class BaseLoader:
    def __init__(self, path, origin, color_dict, valve_dimension, connection_dimension):
        self._path = path
        self._origin = origin
        self._color_dict = color_dict
        self._valve_dimension = valve_dimension
        self._connection_dimension = connection_dimension

    def _get_items(self, key):
        raise NotImplementedError

    def load_config_images(self, scene, images):
        for image in images:
            self._new_image(scene, image)

    def load_switchables(self, scene, valvepath):
        raise NotImplementedError

    def load_pipettes(self, scene):
        raise NotImplementedError

    def load_markup(self, scene):
        raise NotImplementedError

    def load_rects(self, scene):
        for key in RECT_TAGS:
            for b in self._get_items(key):
                c = self._color_dict.get(key, (204, 204, 204))
                klass = KLASS_MAP.get(key, RoundedRectangle)
                self._new_rectangle(
                    scene, b, c, bw=5, origin=self._origin, klass=klass, type_tag=key
                )

    def _new_rectangle(self, *args, **kw):
        raise NotImplementedError

    def _new_label(
        self, scene, label_dict, name, c, layer=1, origin=None, klass=None, **kw
    ):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin
        if klass is None:
            klass = Label

        # tran = label_dict['translation']
        x, y = self._get_translation(label_dict)
        # x, y = 0, 0
        # trans = label.find('translation')
        # if trans is not None:
        #     x, y = map(float, trans.text.split(','))

        c = make_color(c)
        l = klass(
            ox + x,
            oy + y,
            bgcolor=c,
            use_border=label_dict.get("use_border", True),
            name=name,
            text=label_dict.get("text", ""),
            **kw
        )

        font = label_dict.get("font")
        if font is not None:
            l.font = font

        scene.add_item(l, layer=layer)
        return l


# ============= EOF =============================================
