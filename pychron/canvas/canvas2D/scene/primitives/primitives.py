#===============================================================================
# Copyright 2011 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Float, Any, Dict, Bool, Str, Property, List, Int, \
    Color, on_trait_change, String, cached_property, Either
from traitsui.api import View, VGroup, HGroup, Item, Group
from chaco.default_colormaps import color_map_name_dict
from chaco.data_range_1d import DataRange1D
from kiva.fonttools import str_to_font

#============= standard library imports ========================
import math
from numpy import array
#============= local library imports  ==========================
from pychron.core.geometry.convex_hull import convex_hull
# from pyface.image_resource import ImageResource
# from pychron.paths import paths
from kiva.agg.agg import GraphicsContextArray
import Image as PImage


def calc_rotation(x1, y1, x2, y2):
    rise = y2 - y1
    run = x2 - x1

    return math.degrees(math.atan2(rise, run))


def rounded_rect(gc, x, y, width, height, corner_radius):
    with gc:
        gc.translate_ctm(x, y)  # draw a rounded rectangle
        x = y = 0
        gc.begin_path()

        hw = width * 0.5
        hh = height * 0.5
        if hw < corner_radius:
            corner_radius = hw * 0.5
        elif hh < corner_radius:
            corner_radius = hh * 0.5

        gc.move_to(x + corner_radius, y)
        gc.arc_to(x + width, y, x + width, y + corner_radius, corner_radius)
        gc.arc_to(x + width, y + height, x + width - corner_radius, y + height, corner_radius)
        gc.arc_to(x, y + height, x, y, corner_radius)
        gc.arc_to(x, y, x + width + corner_radius, y, corner_radius)
        gc.draw_path()


class Primitive(HasTraits):
    identifier = Str
    identifier_visible = True
    type_tag = Str

    x = Float
    y = Float
    state = False
    selected = False

    default_color = Color('red')
    active_color = Color('(0,255,0)')
    selected_color = Color('blue')

    canvas = Any

    line_width = 1

    name = Str
    name_visible = True

    klass_name = Property

    space = 'data'
    visible = True

    primitives = List
    label = Property
    font = Str('modern 14')
    gfont = Property(depends_on='font')
    #     font = str_to_font('modern 14')

    width = 0
    height = 0

    @cached_property
    def _get_gfont(self):
        return str_to_font(self.font)

    def _get_label(self):
        return '{} {} {}'.format(self.klass_name, self.name, self.identifier)

    def __init__(self, x, y, *args, **kw):
        self.x = x
        self.y = y
        #        self.default_color = (1, 0, 0)
        #        self.active_color = (0, 1, 0)
        super(Primitive, self).__init__(*args, **kw)

    def render(self, gc):

        with gc:
            if self.visible:
                self.set_stroke_color(gc)
                self.set_fill_color(gc)

                gc.set_font(self.gfont)
                gc.set_line_width(self.line_width)

                self._render_(gc)


    def _convert_color(self, c):
        if not isinstance(c, (list, tuple)):
            c = c.red, c.green, c.blue
        c = map(lambda x: x / 255., c)
        return c

    def set_stroke_color(self, gc):
        if self.state:
            c = self._convert_color(self.active_color)
        else:
            c = self._convert_color(self.default_color)

        gc.set_stroke_color(c)

    def set_fill_color(self, gc):
        if self.state:
            c = self._convert_color(self.active_color)
        else:
            c = self._convert_color(self.default_color)
        gc.set_fill_color(c)

    def _render_(self, gc):
        pass

    def adjust(self, dx, dy):
        args = self.canvas.map_data((dx, dy))
        aargs = self.canvas.map_data((0, 0))
        dx = args[0] - aargs[0]
        dy = args[1] - aargs[1]
        self.x += dx
        self.y += dy

    def get_xy(self):
        x, y = self.x, self.y
        offset = 0
        if self.space == 'data':
        #            if self.canvas is None:
        #                print self
            x, y = self.canvas.map_screen([(self.x, self.y)])[0]
            #        offset = self.canvas.offset
            offset = 1
        return x + offset, y + offset

    def get_wh(self):
        w, h = self.width, self.height
        #        w, h = 20, 20
        if self.space == 'data':
            (w, h), (ox, oy) = self.canvas.map_screen([(self.width, self.height), (0, 0)])
            w, h = w - ox, h - oy

        return w, h

    def map_dimension(self, d):
        (w, h), (ox, oy) = self.canvas.map_screen([(d, d), (0, 0)])
        w, h = w - ox, h - oy
        return w

    def set_canvas(self, canvas):
        self.canvas = canvas
        for pi in self.primitives:
            pi.set_canvas(canvas)

    def set_state(self, state):
        self.state = state

    def set_selected(self, selected):
        self.selected = selected

    def _render_name(self, gc, x, y, w, h):
        if self.name and self.name_visible:
            txt = str(self.name)
            self._render_textbox(gc, x, y, w, h, txt)

    def _render_textbox(self, gc, x, y, w, h, txt):
        gc.set_fill_color((0, 0, 0))

        tw, th, _, _ = gc.get_full_text_extent(txt)
        x = x + w / 2. - tw / 2.
        y = y + h / 2. - th / 2.

        self._render_text(gc, txt, x, y)

    def _render_text(self, gc, t, x, y):
        gc.set_text_position(x, y)
        gc.show_text(t)

    @on_trait_change('default_color, active_color, x, y')
    def _refresh_canvas(self):
        self.request_redraw()

    def request_redraw(self):
        if self.canvas:
            # self.canvas._layout_needed = True
            self.canvas.request_redraw()
            # self.canvas._layout_needed = False

    def _get_klass_name(self):
        return self.__class__.__name__.split('.')[-1]

    def traits_view(self):
        g = VGroup(Item('name'), Item('klass_name', label='Type'),
                   Item('default_color'),
                   Item('active_color'),
                   HGroup(Item('x', format_str='%0.3f',
                               #            width=-50
                   ),
                          Item('y', format_str='%0.3f',
                               #     width=-50
                          ))
        )
        cg = self._get_group()
        if cg is not None:
            g = VGroup(g, cg)

        v = View(g)
        return v

    def _get_group(self):
        return


class QPrimitive(Primitive):
    def _convert_color(self, c):
        if not isinstance(c, (list, tuple)):
        #            c = c.red(), c.green(), c.blue()
            c = c.toTuple()

        c = map(lambda x: x / 255., c)
        return c

    def is_in(self, x, y):
        mx, my = self.get_xy()
        w, h = self.get_wh()
        if mx <= x <= (mx + w) and my <= y <= (my + h):
            return True


class Connectable(QPrimitive):
    connections = List

    @on_trait_change('x,y')
    def _update_xy(self):
        for t, c in self.connections:
            c.clear_orientation = True
            func = getattr(c, 'set_{}point'.format(t))
            w, h = self.width, self.height
            func((self.x + w / 2., self.y + h / 2.))
        self.request_redraw()


class Point(QPrimitive):
    radius = Float(1)

    def _get_group(self):
        gs = VGroup('radius')
        return gs

    def _radius_changed(self):
        if self.canvas:
            self.canvas.request_redraw()

    def _render_(self, gc):
        x, y = self.get_xy()
        gc.arc(x, y, self.radius, 0, 360)
        gc.fill_path()

        if self.selected:
            gc.set_stroke_color(self.selected_color)
            gc.arc(x, y, self.radius * (2), 0, 360)
            gc.stroke_path()


class Rectangle(QPrimitive):
    width = 0
    height = 0
    x = 0
    y = 0
    fill = True
    use_border = True

    def _render_(self, gc):
        x, y = self.get_xy()
        w, h = self.get_wh()
        #        gc.set_line_width(self.line_width)
        gc.rect(x, y, w, h)
        if self.fill:
            gc.draw_path()
        #             if self.use_border:
        #                 self._render_border(gc, x, y, w, h)
        else:
            gc.stroke_path()

        self._render_name(gc, x, y, w, h)

    #        if self.name:
    #            t = str(self.name)
    #            tw = gc.get_full_text_extent(t)[0]
    #            x = x + w / 2.0 - tw / 2.0
    #            gc.set_text_position(x, y + h / 2 - 6)
    #            gc.show_text(str(self.name))
    #            gc.draw_path()

    def _render_border(self, gc, x, y, w, h):
    #        gc.set_stroke_color((0, 0, 0))
        gc.rect(x - self.line_width, y - self.line_width,
                w + self.line_width, h + self.line_width
        )
        gc.stroke_path()


class Bordered(Primitive):
    use_border = True
    border_width = 2

    def _get_border_color(self):
        c = self.default_color
        if self.state:
            c = self.active_color

        c = self._convert_color(c)
        c = [ci / (2.) for ci in c]
        if len(c) == 4:
            c[3] = 1

        return c


class RoundedRectangle(Rectangle, Connectable, Bordered):
    corner_radius = 8.0
    display_name = None
    fill = True

    def _render_(self, gc):
        corner_radius = self.corner_radius
        with gc:
            width, height = self.get_wh()
            x, y = self.get_xy()
            if self.fill:
                rounded_rect(gc, x, y, width, height, corner_radius)

            self._render_border(gc, x, y, width, height)

            if self.display_name:
                self._render_textbox(gc, x, y, width, height,
                                     self.display_name)
            elif not self.display_name == '':
                self._render_name(gc, x, y, width, height)


    def _render_border(self, gc, x, y, width, height):
        if self.use_border:

            corner_radius = self.corner_radius
            with gc:
                gc.set_line_width(self.border_width)
                if self.fill:
                    c = self._get_border_color()
                else:
                    c = self.default_color
                    c = self._convert_color(c)
                    gc.set_fill_color((0, 0, 0, 0))

                gc.set_stroke_color(c)
                rounded_rect(gc, x, y, width, height, corner_radius)


class Line(QPrimitive):
    start_point = None
    end_point = None
    screen_rotation = Float
    data_rotation = Float
    width = 1
    height = Property

    def __init__(self, p1=None, p2=None, *args, **kw):

        self.set_startpoint(p1, **kw)
        self.set_endpoint(p2, **kw)

        super(Line, self).__init__(0, 0, *args, **kw)

        #        print self.primitives

    def _get_height(self):
        x, y = self.start_point.get_xy()
        x1, y1 = self.end_point.get_xy()
        return abs(y1 - y)

    def set_endpoint(self, p1, **kw):
        if isinstance(p1, tuple):
            p1 = Point(*p1, **kw)
        self.end_point = p1
        if p1:
            if len(self.primitives) == 2:
                self.primitives[1] = self.end_point
            else:
                self.primitives.append(self.end_point)

    def set_startpoint(self, p1, **kw):
        if isinstance(p1, tuple):
            p1 = Point(*p1, **kw)

        self.start_point = p1

        if p1:
            if len(self.primitives) > 0:
                self.primitives[0] = self.start_point
            else:
                self.primitives.append(self.start_point)

    def set_canvas(self, canvas):
        super(Line, self).set_canvas(canvas)

        self.start_point.set_canvas(canvas)
        if self.end_point:
            self.end_point.set_canvas(canvas)

    def _render_(self, gc):
    #        gc.begin_path()
        gc.set_line_width(self.width)
        if self.start_point and self.end_point:
            x, y = self.start_point.get_xy()
            x1, y1 = self.end_point.get_xy()

            gc.move_to(x, y)
            gc.line_to(x1, y1)
            gc.close_path()
            gc.draw_path()

    def adjust(self, dx, dy):
        self.start_point.adjust(dx, dy)
        self.end_point.adjust(dx, dy)

    def get_length(self):
        dx = self.start_point.x - self.end_point.x
        dy = self.start_point.y - self.end_point.y
        return (dx ** 2 + dy ** 2) ** 0.5

    def calculate_rotation(self):

        x1, y1 = self.start_point.x, self.start_point.y
        x2, y2 = self.end_point.x, self.end_point.y
        a = calc_rotation(x1, y1, x2, y2)

        self.data_rotation = a
        x1, y1 = self.start_point.get_xy()
        x2, y2 = self.end_point.get_xy()

        b = calc_rotation(x1, y1, x2, y2)
        self.screen_rotation = b


class Triangle(QPrimitive):
    draw_text = False

    def __init__(self, *args, **kw):
        super(Triangle, self).__init__(0, 0, **kw)
        self.points = []

    def _render_(self, gc):
        points = self.points
        func = self.canvas.map_screen
        if points:

            as_lines = True
            if as_lines:
                gc.begin_path()
                gc.move_to(*func(points[0][:2]))
                for p in points[1:]:
                    gc.line_to(*func(p[:2]))

                if len(points) == 3:
                    gc.line_to(*func(points[0][:2]))
                gc.close_path()
                gc.stroke_path()
            else:
                f = color_map_name_dict['hot'](DataRange1D(low_setting=0, high_setting=300))
                for x, y, v in points:
                    x, y = func((x, y))
                    gc.set_fill_color(f.map_screen(array([v]))[0])
                    gc.arc(x - 2, y - 2, 2, 0, 360)
                gc.fill_path()

                #                        if self.draw_text:
                gc.set_font_size(9)
                for x, y, v in points:
                    x, y = func((x, y))
                    gc.set_text_position(x + 5, y + 5)
                    gc.show_text('{:0.3f}'.format(v))


class Circle(QPrimitive):
    radius = Float
    fill = False
    fill_color = (1, 1, 0)

    def __init__(self, x, y, radius=10, *args, **kw):
        super(Circle, self).__init__(x, y, *args, **kw)
        self.radius = radius

    def _render_(self, gc):
        x, y = self.get_xy()
        #        print 'asaaaa', self.radius
        r = self.radius
        if self.space == 'data':
            r = self.map_dimension(r)

        gc.arc(x, y, r, 0, 360)
        gc.stroke_path()

        if self.fill:
            gc.set_fill_color(self.fill_color)
            gc.arc(x, y, r, 0, 360)
            gc.fill_path()

        self._render_name(gc, x, y, r / 4., r / 2.)


    def is_in(self, sx, sy):
        x, y = self.get_xy()
        r = self.map_dimension(self.radius)
        if ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5 < r:
            return True

    def _radius_changed(self):
        self.request_redraw()

    def _get_group(self):
        return Item('radius')


class LoadIndicator(Circle):
    degas_indicator = False
    measured_indicator = False
    degas_color = (1, 0.5, 0)
    measured_color = (1, 0, 0)

    #     _text = List
    labnumber_label = None
    weight_label = None
    weight = None
    sample = ''
    irradiation = ''
    note = ''

    def clear_text(self):
        if self.labnumber_label:
            self.primitives.remove(self.labnumber_label)
            self.labnumber_label = None

        if self.weight_label:
            self.primitives.remove(self.weight_label)
            self.weight_label = None

    def add_labnumber_label(self, *args, **kw):
        lb = self.add_text(*args, **kw)
        self.labnumber_label = lb

    def add_weight_label(self, *args, **kw):
        lb = self.add_text(*args, **kw)
        self.weight_label = lb

    def add_text(self, t, ox=0, oy=0, **kw):
    #         x, y = self.get_xy()
        lb = Label(0, 0,
                   text=t,
                   hjustify='center',
                   oy=oy,
                   font='modern 9',
                   use_border=False,
                   **kw)

        self.primitives.append(lb)
        return lb

    #         self._text.append((t, ox, oy))

    def _render_(self, gc):
        super(LoadIndicator, self)._render_(gc)
        #         Circle._render_(self, gc)

        x, y = self.get_xy()
        r = self.map_dimension(self.radius)
        nr = r * 0.25

        if self.degas_indicator:
            gc.set_fill_color(self.degas_color)
            gc.arc(x, y + 2 * nr, nr, 0, 360)
            gc.fill_path()

        if self.measured_indicator:
            gc.set_fill_color(self.measured_color)
            gc.arc(x, y - 2 * nr, nr, 0, 360)
            gc.fill_path()

        for pm in self.primitives:
            pm.x, pm.y = self.x, self.y
            pm.render(gc)

#         if self._text:
#             for ti, _, oy in self._text:
#                 w, _h, _a, _b = gc.get_full_text_extent(ti)
#                 self._render_text(gc, ti, x - w / 2., y + oy)



class CalibrationObject(HasTraits):
    tweak_dict = Dict
    cx = Float
    cy = Float
    rx = Float
    ry = Float

    rotation = Property(depends_on='rx,ry,_rotation')
    _rotation = Float
    center = Property(depends_on='cx,cy')
    scale = Float(1)

    def _set_rotation(self, rot):
        self._rotation = rot

    def _get_rotation(self):
        if not (self.rx and self.rx):
            return self._rotation

        return calc_rotation(self.cx, self.cy, self.rx, self.ry)

    def _get_center(self):
        return self.cx, self.cy

    def set_right(self, x, y):
        self.rx = x
        self.ry = y

    def set_center(self, x, y):
        self.cx = x
        self.cy = y

#    def set_canvas(self, canvas):
#        self.canvas = canvas





class Label(QPrimitive):
    text = String
    use_border = True
    bgcolor = Color('white')
    ox = Float
    oy = Float
    hjustify = 'left'

    def _text_changed(self):
        self.request_redraw()

    def _get_text(self):
        return self.text

    def _render_(self, gc):
        ox, oy = self.get_xy()
        loffset = 3
        x, y = ox + loffset, oy + loffset
        lines = self._get_text().split('\n')

        gc.set_stroke_color((0, 0, 0))
        if self.use_border:
            gc.set_fill_color(self._convert_color(self.bgcolor))
            gc.set_line_width(2)

            offset = 5
            mw = -1
            sh = 10
            for li in lines:
                w, h, _, _ = gc.get_full_text_extent(li)
                mw = max(mw, w + 2 * offset + loffset)
                sh += h
            gc.rect(ox - offset + self.ox,
                    oy - offset + self.oy, mw, sh + loffset)
            gc.draw_path()

        gc.set_fill_color((0, 0, 0))

        gc.set_font(self.gfont)
        for i, li in enumerate(lines[::-1]):
            w, h, _, _ = gc.get_full_text_extent(li)
            x += self.ox
            if self.hjustify == 'center':
                x -= w / 2.
            gc.set_text_position(x, y + self.oy + i * h)
            gc.show_text(li)

    def _get_group(self):
        g = Item('text', style='custom')
        return g


class ValueLabel(Label):
    value = Either(Float, Int, Str)

    def _get_text(self):
        return self.text.format(self.value)


class Indicator(QPrimitive):
    hline_length = 0.5
    vline_length = 0.5
    use_simple_render = Bool(False)
    use_simple_render = Bool(True)
    spot_size = Int(8)
    spot_color = Color('yellow')

    def __init__(self, x, y, *args, **kw):
        super(Indicator, self).__init__(x, y, *args, **kw)
        w = self.hline_length
        self.hline = Line(Point(x - w, y, **kw),
                          Point(x + w, y, **kw), **kw)
        h = self.vline_length
        self.vline = Line(Point(x, y - h, **kw),
                          Point(x, y + h, **kw), **kw)

        self.primitives.append(self.hline)
        self.primitives.append(self.vline)

    def _render_(self, *args, **kw):
        if self.use_simple_render:
            # render a simple square at the current location
            gc = args[0]
            with gc:
                if self.spot_color:
                    sc = self._convert_color(self.spot_color)
                    gc.set_fill_color(sc)
                    gc.set_stroke_color(sc)

                l = self.spot_size
                x, y = self.get_xy()
                hl = l / 2.
                x, y = x - hl, y - hl
                gc.rect(x, y, l, l)
                gc.draw_path()

        else:
            self.hline.render(*args, **kw)
            self.vline.render(*args, **kw)

#    def set_canvas(self, canvas):
#        super(Indicator, self).set_canvas(canvas)
#        self.hline.set_canvas(canvas)
#        self.vline.set_canvas(canvas)

class PointIndicator(Indicator):
    radius = 10
    #    active = Bool(False)
    label_item = Any
    show_label = Bool(True)

    def __init__(self, x, y, *args, **kw):
        super(PointIndicator, self).__init__(x, y, *args, **kw)
        self.circle = Circle(self.x, self.y, *args, **kw)
        self.primitives.append(self.circle)
        if self.identifier:
            self.label_item = Label(self.x, self.y,
                                    text=self.identifier,
                                    visible=self.identifier_visible,
                                    #                               text=str(int(self.identifier[5:]) + 1),
                                    *args, **kw)
            self.primitives.append(self.label_item)

    def set_canvas(self, canvas):
        super(PointIndicator, self).set_canvas(canvas)
        #        for pi in self.primitives:
        #            pi.set_canvas(canvas)
        #
        self.circle.set_canvas(canvas)
        if self.label_item:
            self.label_item.set_canvas(canvas)

    def set_state(self, state):
        self.state = state
        self.hline.state = state
        self.vline.state = state
        self.circle.state = state

    def is_in(self, sx, sy):
        x, y = self.get_xy()
        if ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5 < self.radius:
            return True

    def adjust(self, dx, dy):
        super(PointIndicator, self).adjust(dx, dy)
        self.hline.adjust(dx, dy)
        self.vline.adjust(dx, dy)
        self.circle.adjust(dx, dy)
        self.label.adjust(dx, dy)

    def _render_(self, gc):
        super(PointIndicator, self)._render_(gc)

        if not self.use_simple_render:
            self.circle.render(gc)

            if self.label_item and self.show_label:
                self.label_item.render(gc)

            x, y = self.get_xy()

            if self.state:
                gc.rect(x - self.radius - 1,
                        y - self.radius - 1,
                        2 * self.radius + 1,
                        2 * self.radius + 1
                )

    def _show_label_changed(self):
        self.request_redraw()

    def _get_group(self):
        g = Group(Item('show_label', label='Display label'))
        return g


class Dot(QPrimitive):
    radius = 5

    def _render_(self, gc):
        x, y = self.get_xy()
        gc.arc(x, y, self.radius, 0, 360)
        gc.fill_path()


class PolyLine(QPrimitive):
    points = List
    lines = List
    identifier = Str
    point_klass = PointIndicator
    #    start_point=None
    def __init__(self, x, y, z=0, identifier='', **kw):
        super(PolyLine, self).__init__(x, y, **kw)
        #        self.start_point=PointIndicator(x,y, **kw)
        self.identifier = identifier
        p = self.point_klass(x, y, z=z, identifier=identifier, **kw)
        self.points.append(p)
        self.primitives.append(p)

    def _add_point(self, p2, line_color):
        p1 = self.points[-1]
        l = Line(p1, p2, default_color=line_color)
        self.primitives.append(l)
        self.lines.append(l)

        self.points.append(p2)
        self.primitives.append(p2)

    def add_point(self, x, y, z=0, point_color=(1, 0, 0), line_color=(1, 0, 0),
                  **ptargs):
        p2 = Dot(x, y, z=z, default_color=point_color, **ptargs)
        self._add_point(p2, line_color)

    #        p1 = self.points[-1]
    #        l = Line(p1, p2, default_color=line_color)
    #        self.primitives.append(l)
    #        self.lines.append(l)
    #
    #        self.points.append(p2)
    #        self.primitives.append(p2)

    def _render_(self, gc):
        for pi in self.primitives:
            pi.render(gc)

#        self.start_point.render(gc)
#        for pt in self.points:
#            pt.render(gc)
# #
#        for l in self.lines:
#            l.render(gc)

#    def set_canvas(self, canvas):
#        super(PolyLine,self).set_canvas()
#        for pt in self.points:
#            pt.set_canvas(canvas)
# #
#        for l in self.lines:
#            l.set_canvas(canvas)



class BorderLine(Line, Bordered):
    border_width = 10
    #     border_color = (0, 0, 0.15)
    clear_orientation = False

    def _render_(self, gc):
        gc.save_state()
        gc.set_line_width(self.width + self.border_width)
        #         if self.name in ('C_Bone', 'Bone_C'):
        #             print self.state, self._get_border_color()
        gc.set_stroke_color(self._get_border_color())
        #         gc.set_fill_color(self._get_border_color())
        #             print self.state, self.name, self.default_color, self.active_color
        x, y = self.start_point.get_xy()
        x1, y1 = self.end_point.get_xy()
        # draw border
        gc.move_to(x, y)
        gc.line_to(x1, y1)
        gc.close_path()
        gc.draw_path()
        gc.restore_state()

        #        self.set_stroke_color(gc)
        #        self.set_fill_color(gc)
        #        gc.set_line_width(self.line_width)
        # draw main line
        super(BorderLine, self)._render_(gc)


class Polygon(QPrimitive):
    points = List
    #    lines = List

    identifier = Str
    indicator = None

    def __init__(self, points, ptargs=None, *args, **kw):
        x, y = points[0]
        super(Polygon, self).__init__(x, y, *args, **kw)
        if ptargs is None:
            ptargs = dict()
        for i, (x, y) in enumerate(points):
            self.add_point((x, y), name=str(i),
                           identifier=str(i),
                           **ptargs)

        self.indicator = PointIndicator(x, y,
                                        radius=2,
                                        #                                        canvas=self.canvas,
                                        identifier=self.identifier)
        self.primitives.append(self.indicator)


    def set_canvas(self, c):
        self.canvas = c
        for pi in self.points:
            pi.set_canvas(c)

        self.indicator.set_canvas(c)

    def add_point(self, pt, **kw):
        if isinstance(pt, (tuple, list)):
        #            kw['canvas'] = self.canvas
            pt = Point(*pt, **kw)

        self.points.append(pt)
        self.primitives.append(pt)

    #        # sort points clockwise
    #        xy = array([pi.get_xy() for pi in self.points])
    #        xs, ys = xy.T
    #        cx = xs.mean()
    #        cy = ys.mean()
    #
    #
    #        angles = [(math.atan2(y - cy, x - cx), pi) for pi, x, y in zip(self.points, xs, ys)]
    #        angles = sorted(angles, key=lambda x: x[0])
    #        _, pts = zip(*angles)
    #        self.points = list(pts)

    #        if len(xy) > 2:
    #            self.convex_hull_pts = convex_hull(xy)


    def _render_(self, gc):
        with gc:
            self.indicator.render(gc)

            for pi in self.points:
                pi.render(gc)

            gc.set_stroke_color((0, 0, 1))

            pts = [pi.get_xy() for pi in self.points]
            if len(pts) == 2:
                x0, y0 = pts[0][0], pts[0][1]
                x1, y1 = pts[1][0], pts[1][1]

                x, y = min(x0, x1), min(y0, y1)
                w, h = abs(x0 - x1), abs(y0 - y1)

                gc.rect(x, y, w, h)

            else:
                if len(pts) > 2 and self.use_convex_hull:
                    pts = convex_hull(pts)

                if pts is not None and len(pts) > 2:
                    gc.set_stroke_color(self.default_color)
                    gc.move_to(pts[0][0], pts[0][1])
                    for pi in pts[1:]:
                        gc.line_to(pi[0], pi[1])
                    gc.line_to(pts[0][0], pts[0][1])

            gc.stroke_path()


class Image(QPrimitive):
    search_path = Str
    _cached_image = None
    _image_cache_valid = False
    scale = (1, 1)

    def _render_(self, gc):
        if not self._image_cache_valid:
            self._compute_cached_image()

        if self._cached_image:
            x, y = self.get_xy()
            gc.translate_ctm(x, y)
            gc.scale_ctm(*self.scale)
            gc.draw_image(self._cached_image,
                          #                           rect=(other_component.x, other_component.y,
                          #                                 other_component.width, other_component.height)
            )

    def _compute_cached_image(self):
        pic = PImage.open(self.path)
        data = array(pic)
        if not data.flags['C_CONTIGUOUS']:
            data = data.copy()

        if data.shape[2] == 3:
            kiva_depth = "rgb24"
        elif data.shape[2] == 4:
            kiva_depth = "rgba32"
        else:
            raise RuntimeError, "Unknown colormap depth value: %i" \
                                % data.value_depth

        self._cached_image = GraphicsContextArray(data, pix_format=kiva_depth)
        self._image_cache_valid = True

#============= EOF ====================================
# class CalibrationItem(QPrimitive, CalibrationObject):
#    center = None
#    right = None
#    line = None
#    tool_state = 'move'
#
# #    tweak_dict = Dict
#    def __init__(self, x, y, rotation, *args, **kw):
#        super(CalibrationItem, self).__init__(x, y, *args, **kw)
#
#        self.center = Circle(x, y, 30, canvas=self.canvas)
#
#        r = 10
#        rx = x + r * math.cos(rotation)
#        ry = y + r * math.cos(rotation)
#
#        self.right = Circle(rx, ry, 19, default_color=(1, 1, 1), canvas=self.canvas)
#        self.line = Line(Point(x, y, canvas=self.canvas),
#                          Point(rx, ry, canvas=self.canvas),
#                          default_color=(1, 1, 1),
#                          canvas=self.canvas)
#
#    def _get_rotation(self):
#        return self.line.data_rotation
#
#    def _get_center(self):
#        return self.center.x, self.center.y
#
#    def set_canvas(self, canvas):
#        self.center.set_canvas(canvas)
#        self.right.set_canvas(canvas)
#        self.line.set_canvas(canvas)
#
#    def adjust(self, dx, dy):
#        if self.tool_state == 'move':
#            self.center.adjust(dx, dy)
#            self.right.adjust(dx, dy)
#            self.line.adjust(dx, dy)
#        else:
#            self.right.adjust(dx, dy)
#            self.line.end_point.adjust(dx, dy)
#            self.line.calculate_rotation()
#
#    def _render_(self, gc):
#        self.center.render(gc)
#        self.right.render(gc)
#        self.line.render(gc)
#
#    def is_in(self, event):
#        if self.center.is_in(event):
#            self.tool_state = 'move'
#            return True
#
#        elif self.right.is_in(event):
#            self.tool_state = 'rotate'
#            return True
