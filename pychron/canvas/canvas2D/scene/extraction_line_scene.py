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
from traits.api import Dict
# ============= standard library imports ========================
import weakref
import os
from numpy.core.numeric import Inf
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.canvas_parser import get_volume
from pychron.canvas.canvas2D.scene.primitives.lasers import Laser
from pychron.canvas.canvas2D.scene.primitives.pumps import Turbo
from pychron.canvas.canvas2D.scene.scene import Scene
from pychron.canvas.canvas2D.scene.primitives.primitives import RoundedRectangle, \
    Label, BorderLine, Line, Image, ValueLabel
from pychron.core.helpers.strtools import to_bool
from pychron.canvas.canvas2D.scene.primitives.valves import RoughValve, Valve, Switch
from pychron.extraction_line.valve_parser import ValveParser
from pychron.paths import paths

KLASS_MAP = {'turbo': Turbo, 'laser': Laser}


class ExtractionLineScene(Scene):
    valves = Dict

    def load(self, pathname, configpath, valvepath, canvas):
        print 'fas', canvas
        self.reset_layers()

        origin, color_dict = self._load_config(configpath, canvas)

        cp = self._get_canvas_parser(pathname)

        self._load_switchables(cp, origin, valvepath)

        self._load_rects(cp, origin, color_dict)

        # xv = canvas.view_x_range
        # yv = canvas.view_y_range
        # x, y = xv[0], yv[0]
        # w = xv[1] - xv[0]
        # h = yv[1] - yv[0]

        # brect = Rectangle(x, y, width=w-0.1, height=h-0.1,
        # identifier='bounds_rect',
        # fill=False, line_width=20, default_color=(0, 0, 102))
        # self.add_item(brect)

        self._load_pipettes(cp, origin, color_dict)

        self._load_markup(cp, origin, color_dict)

        # need to load all components that will be connected
        #    before loading connections

        self._load_connections(cp, origin, color_dict)
        self._load_legend(cp, origin, color_dict)

        self.set_canvas(canvas)

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

    def _get_floats(self, elem, name):
        return map(float, elem.find(name).text.split(','))

    def _make_color(self, c):
        if not isinstance(c, str):
            c = ','.join(map(str, map(int, c)))
            c = '({})'.format(c)
        return c

    def _new_rectangle(self, elem, c, bw=3,
                       layer=1,
                       origin=None, type_tag=''):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        key = elem.text.strip()
        display_name = elem.get('display_name', key)
        fill = to_bool(elem.get('fill', 'T'))

        x, y = self._get_floats(elem, 'translation')
        w, h = self._get_floats(elem, 'dimension')

        color = elem.find('color')
        if color is not None:
            c = color.text.strip()
            cobj = self.get_item(c)
            if cobj is not None:
                c = cobj.default_color
        else:
            c = self._make_color(c)
        # if type_tag == 'turbo':
        # klass = Turbo
        # elif
        # else:
        # klass = RoundedRectangle

        klass = KLASS_MAP.get(type_tag, RoundedRectangle)

        rect = klass(x + ox, y + oy, width=w, height=h,
                     name=key,
                     border_width=bw,
                     display_name=display_name,
                     volume=get_volume(elem),
                     default_color=c,
                     type_tag=type_tag,
                     fill=fill)
        font = elem.find('font')
        if font is not None:
            rect.font = font.text.strip()

        if type_tag in ('turbo', 'laser'):
            self.overlays.append(rect)
            rect.scene_visible = False
        # else:

        self.add_item(rect, layer=layer)

        return rect

    def _new_connection(self, conn, key, start, end):

        skey = start.text.strip()
        ekey = end.text.strip()
        try:
            orient = conn.get('orientation')
        except Exception:
            orient = None

        x, y = 0, 0
        sanchor = self.get_item(skey)
        if sanchor:
            x, y = sanchor.x, sanchor.y
            try:
                ox, oy = map(float, start.get('offset').split(','))
            except Exception:
                ox = 1
                oy = sanchor.height / 2.0

            x += ox
            y += oy

        x1, y1 = x, y
        eanchor = self.get_item(ekey)
        if eanchor:
            x1, y1 = eanchor.x, eanchor.y

            try:
                ox, oy = map(float, end.get('offset').split(','))
            except Exception:
                ox = 1
                oy = eanchor.height / 2.0

            x1 += ox
            y1 += oy

        if orient == 'vertical':
            x1 = x
        elif orient == 'horizontal':
            y1 = y

        klass = BorderLine
        l = klass((x, y), (x1, y1),
                  default_color=(204, 204, 204),
                  name=key,
                  width=10)

        ref = weakref.ref(l)
        if sanchor:
            sanchor.connections.append(('start', ref()))
        if eanchor:
            eanchor.connections.append(('end', ref()))

        self.add_item(l, layer=0)

    def _new_line(self, line, name,
                  color=(0, 0, 0), width=2,
                  layer=0,
                  origin=None):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        start = line.find('start')
        if start is not None:
            end = line.find('end')
            if end is not None:
                x, y = map(float, start.text.split(','))
                x1, y1 = map(float, end.text.split(','))

                l = Line((x + ox, y + oy), (x1 + ox, y1 + oy),
                         default_color=color,
                         name=name,
                         width=width)
                self.add_item(l, layer=layer)

    def _new_label(self, label, name, c,
                   layer=1,
                   origin=None, klass=None, **kw):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin
        if klass is None:
            klass = Label
        x, y = 0, 0
        trans = label.find('translation')
        if trans is not None:
            x, y = map(float, trans.text.split(','))

        c = self._make_color(c)
        l = klass(ox + x, oy + y,
                  bgcolor=c,
                  use_border=to_bool(label.get('use_border', 'T')),
                  name=name,
                  text=label.text.strip(),
                  **kw)
        font = label.find('font')
        if font is not None:
            l.font = font.text.strip()

        self.add_item(l, layer=layer)
        return l

    def _new_image(self, image):
        path = image.text.strip()
        if not os.path.isfile(path):
            for di in (paths.app_resources, paths.icons, paths.resources):
                if di:
                    npath = os.path.join(di, path)
                    if os.path.isfile(npath):
                        path = npath
                        break

        if os.path.isfile(path):
            x, y = self._get_floats(image, 'translation')
            scale = None
            if image.find('scale') is not None:
                scale = self._get_floats(image, 'scale')

            im = Image(x, y, path=path, scale=scale)
            self.add_item(im, 0)

    def _load_switchables(self, cp, origin, vpath):
        ox, oy = origin
        ndict = dict()
        vp = ValveParser(vpath)
        for s in cp.get_elements('switch'):
            key = s.text.strip()
            x, y = self._get_floats(s, 'translation')
            radius = 0.75
            r = s.find('radius')
            if r:
                radius = float(r.text.strip())

            v = Switch(x + ox, y + oy, name=key, radius=radius)
            l = s.find('slabel')
            if l is not None:
                label = l.text.strip()
                if l.get('offset'):
                    x, y = map(float, l.get('offset').split(','))
                else:
                    x = 0
                    y = 22
                v.set_label(label, x, y)

            self.add_item(v, layer=1)

        for v in cp.get_elements('valve'):
            key = v.text.strip()
            x, y = self._get_floats(v, 'translation')

            # get the description from valves.xml
            vv = vp.get_valve(key)
            desc = ''
            if vv is not None:
                desc = vv.find('description')
                desc = desc.text.strip() if desc is not None else ''

            v = Valve(x + ox, y + oy,
                      name=key,
                      description=desc,
                      border_width=3)

            # v.translate = x + ox, y + oy
            # sync the states
            if key in self.valves:
                vv = self.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            self.add_item(v, layer=1)
            ndict[key] = v

        for rv in cp.get_elements('rough_valve'):
            key = rv.text.strip()
            x, y = self._get_floats(rv, 'translation')
            v = RoughValve(x + ox, y + oy, name=key)
            self.add_item(v, layer=1)
            ndict[key] = v

        self.valves = ndict

    def _load_markup(self, cp, origin, color_dict):
        """
            labels,images, and lines
        """
        for i, l in enumerate(cp.get_elements('label')):
            if 'label' in color_dict:
                c = color_dict['label']
            else:
                c = (204, 204, 204)
            name = '{:03}'.format(i)
            self._new_label(l, name, c)

        for i, line in enumerate(cp.get_elements('line')):
            self._new_line(line, 'l{}'.format(i))

        for i, image in enumerate(cp.get_elements('image')):
            self._new_image(image)

    def _load_connections(self, cp, origin, color_dict):
        for i, conn in enumerate(cp.get_elements('connection')):
            start = conn.find('start')
            end = conn.find('end')
            name = '{}_{}'.format(start.text, end.text)
            self._new_connection(conn, name, start, end)

    def _load_rects(self, cp, origin, color_dict):
        for key in ('stage', 'laser', 'spectrometer',
                    'turbo', 'getter', 'tank',
                    'ionpump', 'gauge'):
            for b in cp.get_elements(key):
                if key in color_dict:
                    c = color_dict[key]
                else:
                    c = (204, 204, 204)

                self._new_rectangle(b, c, bw=5, origin=origin, type_tag=key)

    def _load_pipettes(self, cp, origin, color_dict):
        if 'pipette' in color_dict:
            c = color_dict['pipette']
        else:
            c = (204, 204, 204)

        for p in cp.get_elements('pipette'):
            rect = self._new_rectangle(p, c, bw=5,
                                       origin=origin, type_tag='pipette')
            # add vlabel
            vlabel = p.find('vlabel')
            if vlabel is not None:
                name = 'vlabel_{}'.format(rect.name)
                ox, oy = 0, 0
                if origin:
                    ox, oy = origin

                self._new_label(vlabel, name, c,
                                origin=(ox + rect.x, oy + rect.y),
                                klass=ValueLabel,
                                value=0)

    def _load_legend(self, cp, origin, color_dict):
        ox, oy = origin
        root = cp.get_root()
        legend = root.find('legend')
        c = (204, 204, 204)

        maxx = -Inf
        minx = Inf
        maxy = -Inf
        miny = Inf

        if legend is not None:
            lox, loy = self._get_floats(legend, 'origin')
            for b in legend.findall('rect'):
                # print b
                rect = self._new_rectangle(b, c, bw=5, origin=(ox + lox, oy + loy),
                                           type_tag='rect',
                                           layer='legend')

                maxx = max(maxx, rect.x)
                maxy = max(maxy, rect.y)
                minx = min(minx, rect.x)
                miny = min(miny, rect.y)

            for i, label in enumerate(legend.findall('llabel')):
                name = '{:03d}label'.format(i)
                ll = self._new_label(label, name, c,
                                     layer='legend',
                                     origin=(ox + lox, oy + loy))
                maxx = max(maxx, ll.x)
                maxy = max(maxy, ll.y)
                minx = min(minx, ll.x)
                miny = min(miny, ll.y)

            for i, line in enumerate(legend.findall('lline')):
                name = '{:03d}line'.format(i)
                self._new_line(line, name,
                               layer='legend',
                               origin=(ox + lox, oy + loy))

            width, height = maxx - minx, maxy - miny
            pad = 0.5
            rect = RoundedRectangle(x=ox + lox - pad,
                                    y=oy + loy - pad,
                                    width=width + 1 + 2 * pad,
                                    height=height + 1 + 2 * pad,
                                    fill=False,
                                    identifier='legend',
                                    border_width=5,
                                    default_color=self._make_color((0, 0, 0)))

            self.add_item(rect, layer='legend')

    def _load_config(self, p, canvas):
        color_dict = dict()
        ox, oy = 0, 0

        if os.path.isfile(p):
            cp = self._get_canvas_parser(p)

            tree = cp.get_tree()
            if tree:
                xv, yv = self._get_canvas_view_range(cp)

                canvas.view_x_range = xv
                canvas.view_y_range = yv
                # get label font
                font = tree.find('font')
                if font is not None:
                    self.font = font.text.strip()

                # get default colors
                for c in tree.findall('color'):
                    t = c.text.strip()
                    k = c.get('tag')

                    t = map(float, t.split(',')) if ',' in t else t

                    if k == 'bgcolor':
                        canvas.bgcolor = t
                    else:
                        color_dict[k] = t

                # get an origin offset

                o = tree.find('origin')
                if o is not None:
                    ox, oy = map(float, o.text.split(','))

                for i, image in enumerate(cp.get_elements('image')):
                    self._new_image(image)

        return (ox, oy), color_dict

# ============= EOF =============================================
