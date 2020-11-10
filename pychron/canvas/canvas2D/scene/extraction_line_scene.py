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

from numpy.core.numeric import Inf
from traits.api import Dict

# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.canvas_parser import get_volume, CanvasParser
from pychron.canvas.canvas2D.scene.primitives.connections import Tee, Fork, Elbow, Connection
from pychron.canvas.canvas2D.scene.primitives.lasers import Laser, CircleLaser
from pychron.canvas.canvas2D.scene.primitives.primitives import Label, BorderLine, Line, Image, ValueLabel
from pychron.canvas.canvas2D.scene.primitives.pumps import Turbo
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle, CircleStage
from pychron.canvas.canvas2D.scene.primitives.valves import RoughValve, Valve, Switch, ManualSwitch
from pychron.canvas.canvas2D.scene.scene import Scene
from pychron.core.helpers.strtools import to_bool
from pychron.core.yaml import yload
from pychron.extraction_line.switch_parser import SwitchParser
from pychron.paths import paths

KLASS_MAP = {'turbo': Turbo, 'laser': Laser, 'circle_stage': CircleStage, 'circle_laser': CircleLaser}

RECT_TAGS = ('stage', 'laser', 'spectrometer',
             'turbo', 'getter', 'tank',
             'ionpump', 'gauge', 'rectangle',
             'circle_stage', 'circle_laser')

SWITCH_TAGS = ('switch', 'valve', 'rough_valve', 'manual_valve')


def get_offset(elem, default=None):
    offset = elem.get('offset')
    if default is None:
        default = 0, 0

    if offset:
        x, y = floatify(offset)
    else:
        x, y = default
    return x, y


def floatify(a, delim=','):
    if not isinstance(a, str):
        a = a.text.strip()

    return [float(i) for i in a.split(delim)]


def colorify(a):
    if not isinstance(a, str):
        a = a.text.strip()

    if a.startswith('0x'):
        a = int(a, 16)
    return a


class ExtractionLineScene(Scene):
    valves = Dict
    rects = Dict

    def load(self, pathname, configpath, valvepath, canvas):
        self.overlays = []
        self.reset_layers()

        origin, color_dict = self._load_config(configpath, canvas)
        if pathname.endswith('.yaml') or pathname.endswith('.yml'):
            klass = YAMLLoader
        else:
            klass = XMLLoader

        loader = klass(pathname, origin, color_dict)

        loader.load_switchables(self, valvepath)
        loader.load_rects(self)
        #
        # loader.load_pipettes()
        # loader.load_markup()
        #
        # # need to load all components that will be connected
        # # before loading connections
        #
        loader.load_connections(self)
        # loader.load_legend()

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
        if os.path.isfile(p):
            cp = self._get_canvas_parser(p)

            tree = cp.get_tree()
            if tree:
                xv, yv = self._get_canvas_view_range(cp)

                canvas.view_x_range = xv
                canvas.view_y_range = yv
                dim = tree.find('valve_dimension')
                if dim is not None:
                    self.valve_dimension = floatify(dim)

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

                for i, image in enumerate(cp.get_elements('image')):
                    self._new_image(cp, image)

        return (ox, oy), color_dict


class BaseLoader:
    valve_dimension = 2, 2

    def __init__(self, path, origin, color_dict):
        self._path = path
        self._origin = origin
        self._color_dict = color_dict

    def _get_items(self, key):
        raise NotImplementedError

    def load_rects(self, scene):
        for key in RECT_TAGS:
            for b in self._get_items(key):
                c = self._color_dict.get(key, (204, 204, 204))
                klass = KLASS_MAP.get(key, RoundedRectangle)
                self._new_rectangle(scene, b, c, bw=5,
                                    origin=self._origin,
                                    klass=klass, type_tag=key)

    def _new_rectangle(self, *args, **kw):
        raise NotImplementedError


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

    def _get_floats(self, v, key='translation', default=None):
        if default is None:
            default = '0,0'

        if isinstance(default, tuple):
            default = ','.join([str(d) for d in default])

        return [float(i) for i in v.get(key, default).split(',')]

    def load_switchables(self, scene, valvepath):
        vp = SwitchParser(valvepath)
        ndict = dict()
        ox, oy = self._origin

        for s in self._yd.get('switch'):
            pass

        for v in self._yd.get('valve'):
            key = v['name'].strip()
            # x, y = self._get_floats(v, 'translation')
            x, y = self._get_translation(v)

            w, h = self._get_floats(v, 'dimension', default=self.valve_dimension)

            # get the description from valves.xml
            vv = vp.get_valve(key)
            desc = ''
            if vv is not None:
                desc = vv.find('description')
                desc = desc.text.strip() if desc is not None else ''

            v = Valve(x + ox, y + oy,
                      name=key,
                      width=w, height=h,
                      description=desc,
                      border_width=3)

            # sync the states
            if key in scene.valves:
                vv = scene.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            scene.add_item(v, layer=1)
            ndict[key] = v

        # scene.valves = ndict

    def load_pipettes(self):
        pass

    def load_markup(self):
        pass

    # need to load all components that will be connected
    # before loading connections

    def load_connections(self, scene):
        for tag, od in (('connection', None),
                        ('hconnection', 'horizontal'),
                        ('vconnection', 'vertical')):
            for conn in self._yd.get(tag, []):
                self._new_connection(scene, conn, orientation_default=od)

        for i, conn in enumerate(self._yd.get('elbow', [])):
            l = self._new_connection(scene, conn, Elbow)
            corner = conn.get('corner', 'ul')
            if corner is not None:
                c = corner.strip()
            l.corner = c

        for tag, klass in (('tee', Tee), ('fork', Fork)):
            for conn in self._yd.get('{}_connection'.format(tag), []):
                self._new_fork(scene, klass, conn)

    def load_legend(self):
        pass

    # private
    def _new_rectangle(self, scene, elem, c, bw=3,
                       layer=1,
                       origin=None, klass=None, type_tag=''):
        if klass is None:
            klass = RoundedRectangle
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        try:
            key = elem['name'].strip()
        except AttributeError:
            key = ''

        display_name = elem.get('display_name', key)
        # print key, display_name
        fill = to_bool(elem.get('fill', 'T'))

        # x, y = self._get_floats(elem, 'translation')
        x, y = self._get_translation(elem)
        w, h = self._get_floats(elem, 'dimension')
        if not w or not h:
            w, h = 5, 5

        color = elem.get('color')
        if color is not None:
            c = color.strip()
            cobj = scene.get_item(c)
            if cobj is not None:
                c = cobj.default_color
            else:
                c = colorify(c)

        else:
            c = scene._make_color(c)

        rect = klass(x + ox, y + oy, width=w, height=h,
                     name=key,
                     border_width=bw,
                     display_name=display_name,
                     volume=elem.get('volume', 0),
                     default_color=c,
                     type_tag=type_tag,
                     fill=fill)
        font = elem.get('font')
        if font is not None:
            rect.font = font.strip()

        if type_tag in ('turbo', 'laser'):
            scene.overlays.append(rect)
            rect.scene_visible = False

        if rect.name:
            scene.rects[rect.name] = rect

        scene.add_item(rect, layer=layer)

        return rect

    def _new_connection(self, scene, conn, klass=None, orientation_default=None):
        if klass is None:
            klass = Connection

        start = conn.get('start')
        end = conn.get('end')

        skey = start['name'].strip()
        ekey = end['name'].strip()
        key = '{}_{}'.format(skey, ekey)

        orient = conn.get('orientation')
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
            ox, oy = get_offset(start, default=default)

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
            ox, oy = get_offset(end, default=default)

            x1 += ox
            y1 += oy

        if orient == 'vertical':
            x1 = x
        elif orient == 'horizontal':
            y1 = y

        connection = klass((x, y), (x1, y1),
                           default_color=(204, 204, 204),
                           name=key,
                           width=10)

        if sanchor:
            sanchor.connections.append(('start', connection))
        if eanchor:
            eanchor.connections.append(('end', connection))

        scene.add_item(connection, layer=0)
        return connection


class XMLLoader(BaseLoader, Scene):

    def __init__(self, *args, **kw):
        super(XMLLoader, self).__init__(*args, **kw)
        print('asdf path', self._path)
        self._cp = CanvasParser(self._path)

    def _new_rectangle(self, scene, elem, c, bw=3,
                       layer=1,
                       origin=None, klass=None, type_tag=''):

        if klass is None:
            klass = RoundedRectangle
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        try:
            key = elem.text.strip()
        except AttributeError:
            key = ''

        display_name = elem.get('display_name', key)
        # print key, display_name
        fill = to_bool(elem.get('fill', 'T'))

        # x, y = self._get_floats(elem, 'translation')
        x, y = self._get_translation(cp, elem)
        w, h = self._get_floats(elem, 'dimension')

        color = elem.find('color')
        if color is not None:
            c = color.text.strip()
            cobj = scene.get_item(c)
            if cobj is not None:
                c = cobj.default_color
            else:
                c = colorify(c)

        else:
            c = scene._make_color(c)
        # if type_tag == 'turbo':
        # klass = Turbo
        # elif
        # else:
        # klass = RoundedRectangle

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
            scene.overlays.append(rect)
            rect.scene_visible = False

        if rect.name:
            scene.rects[rect.name] = rect

        scene.add_item(rect, layer=layer)

        return rect

    def _new_fork(self, scene, klass, conn):
        left = conn.find('left')
        right = conn.find('right')
        mid = conn.find('mid')
        key = '{}-{}-{}'.format(left.text.strip(), mid.text.strip(), right.text.strip())

        height = 4
        dim = conn.find('dimension')
        if dim is not None:
            height = float(dim.text.strip())
        # klass = BorderLine
        tt = klass(0, 0,
                   default_color=(204, 204, 204),
                   name=key, height=height)

        lf = scene.get_item(left.text.strip())
        rt = scene.get_item(right.text.strip())
        mm = scene.get_item(mid.text.strip())
        lf.connections.append(('left', tt))
        rt.connections.append(('right', tt))
        mm.connections.append(('mid', tt))

        def get_xy(item, elem):
            default = item.width / 2., item.height / 2.
            ox, oy = get_offset(elem, default=default)
            return item.x + ox, item.y + oy

        lx, ly = get_xy(lf, left)
        rx, ry = get_xy(rt, right)
        mx, my = get_xy(mm, mid)
        tt.set_points(lx, ly, rx, ry, mx, my)
        scene.add_item(tt, layer=0)

    def _new_connection(self, scene, conn, klass=None, orientation_default=None):
        if klass is None:
            klass = Connection

        start = conn.find('start')
        end = conn.find('end')
        key = '{}_{}'.format(start.text, end.text)

        skey = start.text.strip()
        ekey = end.text.strip()

        orient = conn.get('orientation')
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
            ox, oy = get_offset(start, default=default)

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
            ox, oy = get_offset(end, default=default)

            x1 += ox
            y1 += oy

        if orient == 'vertical':
            x1 = x
        elif orient == 'horizontal':
            y1 = y

        connection = klass((x, y), (x1, y1),
                           default_color=(204, 204, 204),
                           name=key,
                           width=10)

        if sanchor:
            sanchor.connections.append(('start', connection))
        if eanchor:
            eanchor.connections.append(('end', connection))

        scene.add_item(connection, layer=0)
        return connection

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
                x, y = [float(i) for i in start.text.split(',')]
                x1, y1 = [float(i) for i in end.text.split(',')]

                line = Line((x + ox, y + oy), (x1 + ox, y1 + oy),
                            default_color=color,
                            name=name,
                            width=width)
                self.add_item(line, layer=layer)

    def _new_label(self, cp, label, name, c,
                   layer=1,
                   origin=None, klass=None, **kw):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin
        if klass is None:
            klass = Label

        x, y = self._get_translation(cp, label)
        # x, y = 0, 0
        # trans = label.find('translation')
        # if trans is not None:
        #     x, y = map(float, trans.text.split(','))

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

    def _new_image(self, cp, image):
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
            x, y = self._get_translation(cp, image)
            scale = None
            if image.find('scale') is not None:
                scale = self._get_floats(image, 'scale')

            im = Image(x, y, path=path, scale=scale)
            self.add_item(im, 0)

    def load_switchables(self, scene, vpath):
        cp = self._cp
        ox, oy = self._origin
        ndict = dict()
        vp = SwitchParser(vpath)

        for s in cp.get_elements('switch'):
            key = s.text.strip()
            x, y = self._get_translation(cp, s)
            # x, y = self._get_floats(s, 'translation')
            radius = 0.75
            r = s.find('radius')
            if r:
                radius = float(r.text.strip())

            v = Switch(x + ox, y + oy, name=key, radius=radius)
            l = s.find('slabel')
            if l is not None:
                label = l.text.strip()
                # if l.get('offset'):
                #     x, y = list(map(float, l.get('offset').split(',')))
                # else:
                #     x = 0
                #     y = 22
                x, y = get_offset(l, default=(0, 22))
                v.set_label(label, x, y)

            associations = s.findall('association')
            if associations:
                for a in associations:
                    v.associations.append(a.text.strip())

            scene.add_item(v, layer=1)
            ndict[key] = v

        for v in cp.get_elements('valve'):
            key = v.text.strip()
            # x, y = self._get_floats(v, 'translation')
            x, y = self._get_translation(cp, v)
            try:
                w, h = self._get_floats(v, 'dimension')
            except AttributeError:
                w, h = self.valve_dimension
            # get the description from valves.xml
            vv = vp.get_valve(key)
            desc = ''
            if vv is not None:
                desc = vv.find('description')
                desc = desc.text.strip() if desc is not None else ''

            v = Valve(x + ox, y + oy,
                      name=key,
                      width=w, height=h,
                      description=desc,
                      border_width=3)

            # v.translate = x + ox, y + oy
            # sync the states
            if key in scene.valves:
                vv = scene.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            scene.add_item(v, layer=1)
            ndict[key] = v

        for rv in cp.get_elements('rough_valve'):
            key = rv.text.strip()
            # x, y = self._get_floats(rv, 'translation')
            x, y = self._get_translation(cp, rv)
            v = RoughValve(x + ox, y + oy, name=key)
            scene.add_item(v, layer=1)
            ndict[key] = v

        for mv in cp.get_elements('manual_valve'):
            key = mv.text.strip()
            x, y = self._get_translation(cp, mv)
            # x, y = self._get_floats(mv, 'translation')
            vv = vp.get_manual_valve(key)

            desc = ''
            if vv is not None:
                desc = vv.find('description')
                desc = desc.text.strip() if desc is not None else ''
            v = ManualSwitch(x + ox, y + oy,
                             display_name=desc,
                             name=key)
            scene.add_item(v, layer=1)
            ndict[key] = v

        scene.valves = ndict

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
            self._new_label(cp, l, name, c)

        for i, line in enumerate(cp.get_elements('line')):
            self._new_line(line, 'l{}'.format(i))

        for i, image in enumerate(cp.get_elements('image')):
            self._new_image(cp, image)

    def load_connections(self, scene):
        cp = self._cp
        for tag, od in (('connection', None),
                        ('hconnection', 'horizontal'),
                        ('vconnection', 'vertical')):
            for conn in cp.get_elements(tag):
                self._new_connection(scene, conn, orientation_default=od)

        for i, conn in enumerate(cp.get_elements('elbow')):
            l = self._new_connection(scene, conn, Elbow)
            corner = conn.find('corner')
            c = 'ul'
            if corner is not None:
                c = corner.text.strip()
            l.corner = c

        for tag, klass in (('tee', Tee), ('fork', Fork)):
            for conn in cp.get_elements('{}_connection'.format(tag)):
                self._new_fork(scene, klass, conn)

    def _load_pipettes(self, cp, origin, color_dict):
        if 'pipette' in color_dict:
            c = color_dict['pipette']
        else:
            c = (204, 204, 204)

        for p in cp.get_elements('pipette'):
            rect = self._new_rectangle(cp, p, c, bw=5,
                                       origin=origin, type_tag='pipette')
            # add vlabel
            vlabel = p.find('vlabel')
            if vlabel is not None:
                name = 'vlabel_{}'.format(rect.name)
                ox, oy = 0, 0
                if origin:
                    ox, oy = origin

                self._new_label(cp, vlabel, name, c,
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
                rect = self._new_rectangle(cp, b, c, bw=5, origin=(ox + lox, oy + loy),
                                           type_tag='rect',
                                           layer='legend')

                maxx = max(maxx, rect.x)
                maxy = max(maxy, rect.y)
                minx = min(minx, rect.x)
                miny = min(miny, rect.y)

            for i, label in enumerate(legend.findall('llabel')):
                name = '{:03d}label'.format(i)
                ll = self._new_label(cp, label, name, c,
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

# ============= EOF =============================================
