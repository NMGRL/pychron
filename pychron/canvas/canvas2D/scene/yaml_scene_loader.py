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


# ============= EOF =============================================
from random import random

from pychron.canvas.canvas2D.scene.base_scene_loader import (
    BaseLoader,
    colorify,
    get_offset,
    make_color,
)
from pychron.canvas.canvas2D.scene.primitives.connections import (
    Elbow,
    Tee,
    Fork,
    Connection,
)
from pychron.canvas.canvas2D.scene.primitives.primitives import ValueLabel
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle
from pychron.canvas.canvas2D.scene.primitives.valves import (
    Valve,
    RoughValve,
    ManualSwitch,
)
from pychron.canvas.canvas2D.scene.primitives.widgets import Widget
from pychron.core.helpers.strtools import to_bool
from pychron.core.yaml import yload
from pychron.extraction_line.switch_parser import SwitchParser
from pychron.hardware.core.i_core_device import ICoreDevice


class YAMLLoader(BaseLoader):
    def __init__(self, *args, **kw):
        super(YAMLLoader, self).__init__(*args, **kw)
        self._yd = yload(self._path)

    def _get_items(self, key, default=None):
        if default is None:
            default = []

        return self._yd.get(key, default)

    def _get_translation(self, v):
        return self._get_floats(v)

    def _get_floats(self, v, key="translation", default=None):
        if default is None:
            default = "0,0"

        if isinstance(default, (tuple, list)):
            default = ",".join([str(d) for d in default])

        return [float(i) for i in v.get(key, default).split(",")]

    def load_widgets(self, scene, canvas):
        app = canvas.manager.application
        for wi in self._yd.get("widget") or []:
            key = wi["name"]
            x, y = self._get_translation(wi)

            devname = wi["devname"]
            funcname = wi["funcname"]
            dev = app.get_service(ICoreDevice, query="name=='{}'".format(devname))
            if dev:
                func = getattr(dev, funcname)
            else:

                def func():
                    return "NoDevice"

            v = Widget(func, x, y, text="value={}")
            scene.add_item(v)
            scene.widgets[key] = v

    def load_switchables(self, scene, valvepath):
        vp = SwitchParser(valvepath)
        ndict = dict()
        ox, oy = self._origin

        for s in self._yd.get("switch") or []:
            pass

        for v in self._yd.get("valve") or []:
            key = str(v["name"]).strip()
            # x, y = self._get_floats(v, 'translation')
            x, y = self._get_translation(v)
            w, h = self._get_floats(v, "dimension", default=self._valve_dimension)

            # get the description from valves.xml
            vv = vp.get_valve(key)
            desc = ""
            if vv is not None:
                desc = vv.find("description")
                desc = desc.text.strip() if desc is not None else ""

            v = Valve(
                x + ox,
                y + oy,
                name=key,
                width=w,
                height=h,
                description=desc,
                border_width=3,
            )

            # sync the states
            if key in scene.valves:
                vv = scene.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            scene.add_item(v, layer=1)
            ndict[key] = v

        for rv in self._yd.get("rough_valve") or []:
            key = rv["name"].strip()
            # x, y = self._get_floats(rv, 'translation')
            x, y = self._get_translation(rv)
            v = RoughValve(x + ox, y + oy, name=key)
            scene.add_item(v, layer=1)
            ndict[key] = v

        for mv in self._yd.get("manual_valve") or []:
            key = mv["name"].strip()
            x, y = self._get_translation(mv)
            # x, y = self._get_floats(mv, 'translation')
            vv = vp.get_manual_valve(key)
            desc = ""
            if vv is not None:
                desc = vv.find("description")
                desc = desc.text.strip() if desc is not None else ""
            v = ManualSwitch(x + ox, y + oy, display_name=desc, name=key)

            scene.add_item(v, layer=1)
            ndict[key] = v

        scene.valves = ndict

    def load_pipettes(self, scene):
        origin = self._origin
        c = self._color_dict.get("pipette", (204, 204, 204))
        ox, oy = origin
        for p in self._yd.get("pipette") or []:
            rect = self._new_rectangle(scene, p, c, origin=origin, type_tag="pipette")

            vlabel = p.get("vlabel")
            if vlabel is not None:
                name = "vlabel_{}".format(rect.name)
                self._new_label(
                    scene,
                    vlabel,
                    name,
                    c,
                    origin=(ox + rect.x, oy + rect.y),
                    klass=ValueLabel,
                    value=0,
                )

    def load_markup(self, scene):
        pass

    # need to load all components that will be connected
    # before loading connections

    def load_connections(self, scene):
        for tag, od in (
            ("connection", None),
            ("hconnection", "horizontal"),
            ("vconnection", "vertical"),
        ):
            for conn in self._yd.get(tag, []):
                self._new_connection(scene, conn, orientation_default=od)

        for i, conn in enumerate(self._yd.get("elbow", [])):
            l = self._new_connection(scene, conn, Elbow)
            corner = conn.get("corner", "ul")
            if corner is not None:
                c = corner.strip()
            l.corner = c

        for tag, klass in (("tee", Tee), ("fork", Fork)):
            for conn in self._yd.get("{}_connection".format(tag), []):
                self._new_fork(scene, klass, conn)

    def load_legend(self, scene):
        pass

    # private
    def _new_fork(self, scene, klass, conn):
        left = conn.get("left")
        right = conn.get("right")
        mid = conn.get("mid")
        lname = str(left["name"]).strip()
        mname = str(mid["name"]).strip()
        rname = str(right["name"]).strip()
        key = "{}-{}-{}".format(lname, mname, rname)

        height = 4
        dim = conn.get("dimension")
        if dim is not None:
            height = float(dim.strip())
        # klass = BorderLine
        tt = klass(0, 0, default_color=(204, 204, 204), name=key, height=height)

        lf = scene.get_item(lname)
        rt = scene.get_item(rname)
        mm = scene.get_item(mname)
        lf.connections.append(("left", tt))
        rt.connections.append(("right", tt))
        mm.connections.append(("mid", tt))

        def get_xy(item, elem):
            default = item.width / 2.0, item.height / 2.0
            ox, oy, txt = get_offset(elem, default=default)
            return item.x + ox, item.y + oy

        lx, ly = get_xy(lf, left)
        rx, ry = get_xy(rt, right)
        mx, my = get_xy(mm, mid)
        tt.set_points(lx, ly, rx, ry, mx, my)
        scene.add_item(tt, layer=0)

    def _new_rectangle(
        self, scene, elem, c, bw=3, layer=1, origin=None, klass=None, type_tag=""
    ):
        if klass is None:
            klass = RoundedRectangle

        if origin is None:
            ox, oy = self._origin
        else:
            ox, oy = origin

        try:
            key = elem["name"].strip()
        except AttributeError:
            key = ""

        display_name = elem.get("display_name", key)
        # print key, display_name
        fill = to_bool(elem.get("fill", "T"))

        # x, y = self._get_floats(elem, 'translation')
        x, y = self._get_translation(elem)
        w, h = self._get_floats(elem, "dimension")
        if not w or not h:
            w, h = 5, 5

        color = elem.get("color")
        if color is not None:
            c = color.strip()
            cobj = scene.get_item(c)
            if cobj is not None:
                c = cobj.default_color
            else:
                c = colorify(c)

        else:
            c = make_color(c)

        rect = klass(
            x + ox,
            y + oy,
            width=w,
            height=h,
            name=key,
            border_width=bw,
            display_name=display_name,
            volume=elem.get("volume", 0),
            default_color=c,
            type_tag=type_tag,
            fill=fill,
            use_symbol=elem.get("use_symbol", False),
        )
        font = elem.get("font")
        if font is not None:
            rect.font = font.strip()

        if type_tag in ("turbo", "laser"):
            scene.overlays.append(rect)
            rect.scene_visible = False

        if rect.name:
            scene.rects[rect.name] = rect

        scene.add_item(rect, layer=layer)

        return rect

    def _new_image(self, scene, image):
        pass

    def _new_connection(self, scene, conn, klass=None, orientation_default=None):
        if klass is None:
            klass = Connection

        start = conn.get("start")
        end = conn.get("end")

        skey = str(start["name"]).strip()
        ekey = str(end["name"]).strip()
        key = "{}_{}".format(skey, ekey)

        orient = conn.get("orientation")
        if orient is None:
            orient = orientation_default

        x, y = 0, 0
        sox, soy, start_offset = 0, 0, "0,0"
        sanchor = scene.get_item(skey)
        if sanchor:
            x, y = sanchor.x, sanchor.y
            default = sanchor.width / 2.0, sanchor.height / 2.0
            sox, soy, start_offset = get_offset(start, default=default)

            x += sox
            y += soy

        x1, y1 = x, y
        eox, eoy, end_offset = 0, 0, "0,0"
        eanchor = scene.get_item(ekey)
        if eanchor:
            x1, y1 = eanchor.x, eanchor.y
            default = eanchor.width / 2.0, eanchor.height / 2.0
            eox, eoy, end_offset = get_offset(end, default=default)
            x1 += eox
            y1 += eoy

        if orient == "vertical":
            x1 = x
        elif orient == "horizontal":
            y1 = y

        dimension = float(conn.get("dimension", self._connection_dimension))
        connection = klass(
            (x, y),
            (x1, y1),
            orientation=orient,
            start=skey,
            end=ekey,
            start_offset=start_offset,
            end_offset=end_offset,
            default_color=(204, 204, 204),
            name=key,
            width=dimension,
        )

        if sanchor:
            sanchor.connections.append(("start", connection))
        if eanchor:
            eanchor.connections.append(("end", connection))

        scene.add_item(connection, layer=0)
        return connection
