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
import os

from numpy import Inf

from pychron.canvas.canvas2D.scene.canvas_parser import CanvasParser, get_volume
from pychron.canvas.canvas2D.scene.base_scene_loader import (
    BaseLoader,
    colorify,
    get_offset,
    make_color,
)
from pychron.canvas.canvas2D.scene.primitives.connections import (
    Connection,
    Elbow,
    Tee,
    Fork,
    RConnection,
)
from pychron.canvas.canvas2D.scene.primitives.primitives import (
    Line,
    Image,
    ValueLabel,
)
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle
from pychron.canvas.canvas2D.scene.primitives.valves import (
    Switch,
    Valve,
    RoughValve,
    ManualSwitch,
)
from pychron.canvas.canvas2D.scene.primitives.widgets import Widget
from pychron.core.helpers.strtools import to_bool
from pychron.extraction_line.switch_parser import SwitchParser
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.paths import paths


class XMLLoader(BaseLoader):
    def __init__(self, *args, **kw):
        super(XMLLoader, self).__init__(*args, **kw)
        self._cp = CanvasParser(self._path)

    def _get_floats(self, elem, name):
        return [float(i) for i in elem.find(name).text.split(",")]

    def _get_translation(self, elem, name="translation"):
        if isinstance(elem, dict):
            elem = elem["translation"]

        x, y = elem.find(name).text.split(",")
        try:
            x = float(x)
        except ValueError:
            x = self._get_parameteric_translation(x)

        try:
            y = float(y)
        except ValueError:
            y = self._get_parameteric_translation(y)

        return x, y

    def _get_parameteric_translation(self, tag):
        v = 0
        offset = 0
        if "+" in tag:
            tag, offset = tag.split("+")
        elif "-" in tag:
            tag, offset = tag.split("-")

        offset = int(offset)
        for p in self._cp.get_elements("param"):
            if p.text.strip() == tag:
                e = p.find("value")
                v = e.text.strip()

        return float(v) + offset

    def _get_items(self, *args, **kw):
        return self._cp.get_elements(*args, **kw)

    def _new_rectangle(
        self, scene, elem, c, bw=3, layer=1, origin=None, klass=None, type_tag=""
    ):
        if klass is None:
            klass = RoundedRectangle
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        try:
            key = elem.text.strip()
        except AttributeError:
            key = ""

        display_name = elem.get("display_name", key)
        fill = to_bool(elem.get("fill", "T"))
        border_width = elem.get("border_width", bw)
        if border_width:
            border_width = int(border_width)

        x, y = self._get_translation(elem)
        w, h = self._get_floats(elem, "dimension")

        color = elem.find("color")
        if color is not None:
            c = color.text.strip()
            cobj = scene.get_item(c)
            if cobj is not None:
                c = cobj.default_color
            else:
                c = colorify(c)

        else:
            c = make_color(c)
        # if type_tag == 'turbo':
        # klass = Turbo
        # elif
        # else:
        # klass = RoundedRectangle

        rect = klass(
            x + ox,
            y + oy,
            width=w,
            height=h,
            name=key,
            border_width=border_width,
            display_name=display_name,
            volume=get_volume(elem),
            default_color=c,
            type_tag=type_tag,
            fill=fill,
        )

        font = elem.find("font")
        if font is not None:
            rect.font = font.text.strip()

        if type_tag in ("turbo", "laser", "ionpump"):
            scene.overlays.append(rect)
            rect.scene_visible = False
            rect.use_symbol = to_bool(elem.get("use_symbol", key))

        if rect.name:
            scene.rects[rect.name] = rect

        scene.add_item(rect, layer=layer)

        return rect

    def _new_fork(self, scene, klass, conn):
        left = conn.find("left")
        right = conn.find("right")
        mid = conn.find("mid")
        key = "{}-{}-{}".format(left.text.strip(), mid.text.strip(), right.text.strip())

        height = 4
        dim = conn.find("dimension")
        if dim is not None:
            height = float(dim.text.strip())
        # klass = BorderLine
        tt = klass(0, 0, default_color=(204, 204, 204), name=key, height=height)

        lf = scene.get_item(left.text.strip())
        rt = scene.get_item(right.text.strip())
        mm = scene.get_item(mid.text.strip())
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

    def _new_connection(self, scene, conn, klass=None, orientation_default=None):
        if klass is None:
            klass = Connection

        start = conn.find("start")
        end = conn.find("end")
        key = "{}_{}".format(start.text, end.text)

        skey = start.text.strip()
        ekey = end.text.strip()

        orient = conn.get("orientation")
        if orient is None:
            orient = orientation_default

        x, y = 0, 0
        sanchor = scene.get_item(skey)
        if sanchor:
            x, y = sanchor.x, sanchor.y
            # try:
            #     ox, oy = list(map(float, start.get('offset').split(',')))
            # except AttributeError:
            #     ox = sanchor.width / 2.0
            #     oy = sanchor.height / 2.0

            default = sanchor.width / 2.0, sanchor.height / 2.0
            ox, oy, txt = get_offset(start, default=default)

            x += ox
            y += oy

        x1, y1 = x, y
        eanchor = scene.get_item(ekey)
        if eanchor:
            x1, y1 = eanchor.x, eanchor.y

            # try:
            #     ox, oy = list(map(float, end.get('offset').split(',')))
            # except AttributeError:
            #     ox = eanchor.width / 2.0
            #     oy = eanchor.height / 2.0
            default = eanchor.width / 2.0, eanchor.height / 2.0
            ox, oy, txt = get_offset(end, default=default)

            x1 += ox
            y1 += oy

        if orient == "vertical":
            x1 = x
        elif orient == "horizontal":
            y1 = y

        connection = klass((x, y), (x1, y1), default_color=(204, 204, 204), name=key)

        if sanchor:
            sanchor.connections.append(("start", connection))
        if eanchor:
            eanchor.connections.append(("end", connection))

        scene.add_item(connection, layer=0)
        return connection

    def _new_line(
        self, scene, line, name, color=(0, 0, 0), width=2, layer=0, origin=None
    ):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        start = line.find("start")
        if start is not None:
            end = line.find("end")
            if end is not None:
                x, y = [float(i) for i in start.text.split(",")]
                x1, y1 = [float(i) for i in end.text.split(",")]

                line = Line(
                    (x + ox, y + oy),
                    (x1 + ox, y1 + oy),
                    default_color=color,
                    name=name,
                    width=width,
                )
                scene.add_item(line, layer=layer)

    def _new_image(self, scene, image):
        path = image.text.strip()
        if not os.path.isfile(path):
            for di in (paths.app_resources, paths.icons, paths.resources):
                if di:
                    npath = os.path.join(di, path)
                    if os.path.isfile(npath):
                        path = npath
                        break

        if os.path.isfile(path):
            # x, y = self._get_floats(image, 'translation')
            x, y = self._get_translation(image)
            scale = None
            if image.find("scale") is not None:
                scale = self._get_floats(image, "scale")

            im = Image(x, y, path=path, scale=scale)
            scene.add_item(im, 0)

    def _new_label(self, scene, label, name, c, **kw):
        label_dict = {}
        label_dict["use_border"] = to_bool(label.get("use_border", "T"))
        label_dict["text"] = label.text.strip()
        label_dict["translation"] = label

        font = label.find("font")
        if font is not None:
            label_dict["font"] = font.text.strip()

        return super(XMLLoader, self)._new_label(scene, label_dict, name, c, **kw)

    def load_widgets(self, scene, canvas):
        app = canvas.manager.application
        for wi in self._cp.get_elements("widget"):
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

    def load_switchables(self, scene, vpath):
        cp = self._cp
        ox, oy = self._origin
        ndict = dict()
        vp = SwitchParser(vpath)

        for s in cp.get_elements("switch"):
            key = s.text.strip()
            x, y = self._get_translation(s)
            # x, y = self._get_floats(s, 'translation')
            radius = 0.75
            r = s.find("radius")
            if r:
                radius = float(r.text.strip())

            v = Switch(x + ox, y + oy, name=key, radius=radius)
            l = s.find("slabel")
            if l is not None:
                label = l.text.strip()
                # if l.get('offset'):
                #     x, y = list(map(float, l.get('offset').split(',')))
                # else:
                #     x = 0
                #     y = 22
                x, y, txt = get_offset(l, default=(0, 22))
                v.set_label(label, x, y)

            associations = s.findall("association")
            if associations:
                for a in associations:
                    v.associations.append(a.text.strip())

            scene.add_item(v, layer=1)
            ndict[key] = v

        for v in cp.get_elements("valve"):
            key = v.text.strip()
            # x, y = self._get_floats(v, 'translation')
            x, y = self._get_translation(v)
            try:
                w, h = self._get_floats(v, "dimension")
            except AttributeError:
                w, h = self._valve_dimension
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

            # v.translate = x + ox, y + oy
            # sync the states
            if key in scene.valves:
                vv = scene.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            scene.add_item(v, layer=1)
            ndict[key] = v

        for rv in cp.get_elements("rough_valve"):
            key = rv.text.strip()
            # x, y = self._get_floats(rv, 'translation')
            x, y = self._get_translation(rv)
            v = RoughValve(x + ox, y + oy, name=key)
            scene.add_item(v, layer=1)
            ndict[key] = v

        for mv in cp.get_elements("manual_valve"):
            key = mv.text.strip()
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

    def load_markup(self, scene):
        """
        labels,images, and lines
        """
        cp = self._cp
        color_dict = self._color_dict

        for i, l in enumerate(cp.get_elements("label")):
            if "label" in color_dict:
                c = color_dict["label"]
            else:
                c = (204, 204, 204)
            name = "{:03}".format(i)
            self._new_label(scene, l, name, c)

        for i, line in enumerate(cp.get_elements("line")):
            self._new_line(scene, line, "l{}".format(i))

        for i, image in enumerate(cp.get_elements("image")):
            self._new_image(scene, image)

    def load_connections(self, scene):
        cp = self._cp
        for tag, od in (
            ("connection", None),
            ("hconnection", "horizontal"),
            ("vconnection", "vertical"),
        ):
            for conn in cp.get_elements(tag):
                self._new_connection(scene, conn, orientation_default=od)

        for i, conn in enumerate(cp.get_elements("rconnection")):
            c = self._new_connection(scene, conn, RConnection)

        for i, conn in enumerate(cp.get_elements("elbow")):
            l = self._new_connection(scene, conn, Elbow)
            corner = conn.find("corner")
            c = "ul"
            if corner is not None:
                c = corner.text.strip()
            l.corner = c

        for tag, klass in (("tee", Tee), ("fork", Fork)):
            for conn in cp.get_elements("{}_connection".format(tag)):
                self._new_fork(scene, klass, conn)

    def load_pipettes(self, scene):
        color_dict = self._color_dict
        cp = self._cp
        origin = self._origin
        ox, oy = 0, 0
        if origin:
            ox, oy = origin

        c = color_dict.get("pipette", (204, 204, 204))

        for p in cp.get_elements("pipette"):
            rect = self._new_rectangle(
                scene, p, c, bw=5, origin=origin, type_tag="pipette"
            )
            # add vlabel
            vlabel = p.find("vlabel")
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

    def load_legend(self, scene):
        ox, oy = self._origin
        cp = self._cp
        root = cp.get_root()
        legend = root.find("legend")
        c = (204, 204, 204)

        maxx = -Inf
        minx = Inf
        maxy = -Inf
        miny = Inf

        if legend is not None:
            lox, loy = self._get_floats(legend, "origin")
            for b in legend.findall("rect"):
                # print b
                rect = self._new_rectangle(
                    scene,
                    b,
                    c,
                    bw=5,
                    origin=(ox + lox, oy + loy),
                    type_tag="rect",
                    layer="legend",
                )

                maxx = max(maxx, rect.x)
                maxy = max(maxy, rect.y)
                minx = min(minx, rect.x)
                miny = min(miny, rect.y)

            for i, label in enumerate(legend.findall("llabel")):
                name = "{:03d}label".format(i)
                ll = self._new_label(
                    scene, label, name, c, layer="legend", origin=(ox + lox, oy + loy)
                )
                maxx = max(maxx, ll.x)
                maxy = max(maxy, ll.y)
                minx = min(minx, ll.x)
                miny = min(miny, ll.y)

            for i, line in enumerate(legend.findall("lline")):
                name = "{:03d}line".format(i)
                self._new_line(
                    scene, line, name, layer="legend", origin=(ox + lox, oy + loy)
                )

            width, height = maxx - minx, maxy - miny
            pad = 0.5
            rect = RoundedRectangle(
                x=ox + lox - pad,
                y=oy + loy - pad,
                width=width + 1 + 2 * pad,
                height=height + 1 + 2 * pad,
                fill=False,
                identifier="legend",
                border_width=5,
                default_color=make_color((0, 0, 0)),
            )

            scene.add_item(rect, layer="legend")

    def load_stateables(self, scene):
        color_dict = self._color_dict
        cp = self._cp
        for key in ("gate", "funnel"):
            for b in cp.get_elements(key):
                if key in color_dict:
                    c = color_dict[key]
                else:
                    c = (204, 204, 204)
                rect = self._new_rectangle(scene, b, c, bw=5, type_tag=key)
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
