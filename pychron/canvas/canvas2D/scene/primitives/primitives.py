# ===============================================================================
# Copyright 2011 Jake Ross
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
import time

from traits.api import HasTraits, Float, Any, Dict, Bool, Str, Property, List, Int, \
    Color, String, Either
from traitsui.api import VGroup, Item, Group
from chaco.default_colormaps import color_map_name_dict
from chaco.data_range_1d import DataRange1D


# ============= standard library imports ========================
import math
from numpy import array
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.base import QPrimitive, Primitive
from pychron.core.geometry.convex_hull import convex_hull
from kiva.agg.agg import GraphicsContextArray
import Image as PImage


def calc_rotation(x1, y1, x2, y2):
    rise = y2 - y1
    run = x2 - x1

    return math.degrees(math.atan2(rise, run))


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

        x, y = self.get_xy(clear_layout_needed=False)
        w, h = self.get_wh()

        # gc.set_line_width(self.line_width)
        gc.rect(x, y, w, h)
        if self.fill:
            gc.draw_path()
        # if self.use_border:
        # self._render_border(gc, x, y, w, h)
        else:
            gc.stroke_path()

        self._render_name(gc, x, y, w, h)

    def _render_border(self, gc, x, y, w, h):
        # gc.set_stroke_color((0, 0, 0))
        gc.rect(x - self.line_width, y - self.line_width,
                w + self.line_width, h + self.line_width)
        gc.stroke_path()


class Bordered(Primitive):
    use_border = True
    border_width = 2

    def _get_border_color(self):
        c = self.default_color
        if self.state:
            c = self.active_color

        c = self._convert_color(c)
        c = [ci / 2. for ci in c]
        if len(c) == 4:
            c[3] = 1

        return c


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

        # print self.primitives

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

    def _render_(self, gc):
        # gc.begin_path()
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

                # if self.draw_text:
                gc.set_font_size(9)
                for x, y, v in points:
                    x, y = func((x, y))
                    gc.set_text_position(x + 5, y + 5)
                    gc.show_text('{:0.3f}'.format(v))


class Circle(QPrimitive):
    radius = Float
    fill = Bool
    fill_color = Any

    def __init__(self, x, y, radius=10, *args, **kw):
        super(Circle, self).__init__(x, y, *args, **kw)
        self.radius = radius

    def _render_(self, gc):
        x, y = self.get_xy()
        # print 'asaaaa', self.radius
        r = self.radius
        if self.space == 'data':
            r = self.map_dimension(r)

        gc.arc(x, y, r, 0, 360)
        gc.stroke_path()

        if self.fill:
            if self.fill_color:
                gc.set_fill_color(self._convert_color(self.fill_color))
            gc.arc(x, y, r, 0, 360)
            gc.fill_path()

        self._render_name(gc, x + self.name_offsetx, y + self.name_offsety, r / 4., r / 2.)

    def is_in(self, sx, sy):
        x, y = self.get_xy()
        r = self.map_dimension(self.radius)
        # print ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5, r
        return ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5 < r

    def _radius_changed(self):
        self.request_redraw()

    def _get_group(self):
        return Item('radius')


class Span(Line):
    hole_dim = 1
    hole_spacing = 1
    continued_line = False
    # fill = (0.78,0.78, 0.78,1)
    fill = None  # (0.78,0.78, 0.78,1)

    def _render_(self, gc):
        x, y = self.start_point.get_xy()
        x1, y1 = self.end_point.get_xy()
        hd = self.map_dimension(self.hole_dim)
        hs = self.map_dimension(self.hole_spacing / 2.0)
        w = x1 - x + 4
        x0 = x - hd
        y0 = y - hd
        with gc:
            if self.fill:
                self._render_boxes(gc, x0, y0, w, hd, hs)
            else:
                self._render_lines(gc, x0, y0, w, hd)

    def _render_boxes(self, gc, x, y, w, hd, hs):
        x -= 2
        gc.set_stroke_color(self.fill)
        gc.set_fill_color(self.fill)
        # v=(hs-hd)/2.0
        if self.continued_line == 1:
            gc.rect(x, y - hd, w + 2 * hd, 2 * hs)
        elif self.continued_line == 2:
            gc.rect(x, y - hd, w + 2 * hd, 2 * hs)
        elif self.continued_line == 3:
            gc.rect(x, y - hd + 4, w + 2 * hd, 2 * hs - 2)
        else:
            gc.rect(x, y - hd + 4, w + 2 * hd, 2 * hs - 4)

        gc.draw_path()

        # gc.set_stroke_color((1,0,0,1))
        # gc.move_to(x, y-hd)
        # gc.line_to(x+10, y-hd)
        # gc.stroke_path()

    def _render_lines(self, gc, x, y, w, hd):
        x -= 2
        y -= 2
        if self.continued_line:
            if self.continued_line == 1:
                gc.move_to(x + w + 2 * hd, y + 2 * hd + 4)
                gc.line_to(x, y + 2 * hd + 4)
                gc.line_to(x, y)
                gc.line_to(x + w + 2 * hd, y)
            elif self.continued_line == 2:
                gc.move_to(x, y + 2 * hd + 4)
                gc.line_to(x + w + 2 * hd, y + 2 * hd + 4)
                gc.line_to(x + w + 2 * hd, y)
                gc.line_to(x, y)
            elif self.continued_line == 3:
                gc.move_to(x, y + 2 * hd + 4)
                gc.line_to(x + w + 2 * hd, y + 2 * hd + 4)
                gc.move_to(x + w + 2 * hd, y)
                gc.line_to(x, y)
        else:
            gc.rect(x, y, w + 2 * hd, 2 * hd + 4)
        gc.stroke_path()


class LoadIndicator(Circle):
    degas_indicator = False
    measured_indicator = False
    degas_color = Color('orange')
    measured_color = Color('purple')
    default_color = 'black'
    fill_color = Color('lightblue')
    # _text = List
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
        if self.labnumber_label:
            self.primitives.remove(self.labnumber_label)

        lb = self.add_text(*args, **kw)
        self.labnumber_label = lb

    def add_weight_label(self, *args, **kw):
        if self.weight_label:
            self.primitives.remove(self.weight_label)

        lb = self.add_text(*args, **kw)
        self.weight_label = lb

    def add_text(self, t, ox=0, oy=0, **kw):
        # x, y = self.get_xy()
        lb = Label(0, 0,
                   text=t,
                   hjustify='center',
                   offset_y=oy,
                   font='modern 9',
                   use_border=False,
                   **kw)

        self.primitives.append(lb)
        return lb

    # self._text.append((t, ox, oy))

    def _render_(self, gc):
        c = (0, 0, 0)
        if self.fill and self.fill_color and sum(self.fill_color.toTuple()[:3]) < 1.5:
            c = (255, 255, 255)

        self.text_color = c
        for p in self.primitives:
            p.text_color = c

        x, y = self.get_xy()
        r = self.radius
        if self.space == 'data':
            r = self.map_dimension(r)

        self.name_offsetx = r - 2
        self.name_offsety = r - 2

        if self.state:
            with gc:
                gc.set_stroke_color(self._convert_color(self.active_color))
                gc.set_line_width(2)
                gc.arc(x, y, r, 0, 360)
                gc.stroke_path()

        nr = r * 0.25

        super(LoadIndicator, self)._render_(gc)
        if self.degas_indicator:
            gc.set_fill_color(self._convert_color(self.degas_color))
            gc.arc(x, y + 2 * nr, nr, 0, 360)
            gc.fill_path()

        if self.measured_indicator:
            gc.set_fill_color(self._convert_color(self.measured_color))
            gc.arc(x, y - 2 * nr, nr, 0, 360)
            gc.fill_path()

        # print self.primitives
        for pm in self.primitives:
            pm.x, pm.y = self.x, self.y
            pm.render(gc)


# if self._text:
# for ti, _, oy in self._text:
# w, _h, _a, _b = gc.get_full_text_extent(ti)
# self._render_text(gc, ti, x - w / 2., y + oy)



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


# def set_canvas(self, canvas):
# self.canvas = canvas


class Label(QPrimitive):
    text = String
    use_border = True
    bgcolor = Color('white')
    # ox = Float
    # oy = Float
    hjustify = 'left'
    vjustify = 'bottom'
    soffset_x = Float
    soffset_y = Float
    label_offsety = Float
    # def __init__(self, *args, **kw):
    # super(Label, self).__init__(*args, **kw)
    # self.text_color = 'black'

    def _text_changed(self):
        self.request_redraw()

    def _get_text(self):
        return self.text

    def _render_(self, gc):
        ox, oy = self.get_xy()
        loffset = 3
        x, y = ox + loffset, oy + loffset
        lines = self._get_text().split('\n')

        gc.set_stroke_color(self._convert_color(self.default_color))

        offset = 0
        mw = -1
        sh = 0
        for li in lines:
            w, h, _, _ = gc.get_full_text_extent(li)
            mw = max(mw, w + 6)
            sh += h

        with gc:
            if self.vjustify == 'center':
                gc.translate_ctm(0, -sh / 2.0)
            gc.translate_ctm(0, self.label_offsety)

            gc.set_stroke_color((0, 0, 0))
            if self.use_border:
                gc.set_fill_color(self._convert_color(self.bgcolor))
                gc.set_line_width(2)
                gc.rect(ox + offset + self.soffset_x,
                        oy + offset + self.soffset_y, mw, 5 + sh)
                gc.draw_path()

            # gc.set_fill_color((0, 0, 0))

            c = self.text_color if self.text_color else self.default_color
            gc.set_fill_color(self._convert_color(c))
            # gc.set_stroke_color(self._convert_color(self.default_color))

            gc.set_font(self.gfont)
            for i, li in enumerate(lines[::-1]):
                w, h, _, _ = gc.get_full_text_extent(li)
                x += self.soffset_x
                if self.hjustify == 'center':
                    x -= w / 2.
                gc.set_text_position(x, y + self.soffset_y + i * h)
                gc.show_text(li)

    def _get_group(self):
        g = Item('text', style='custom')
        return g


class ValueLabel(Label):
    value = Either(Float, Int, Str)

    def _get_text(self):
        return self.text.format(self.value)


class Indicator(QPrimitive):
    hline_length = 0.1
    vline_length = 0.1
    # use_simple_render = Bool(False)
    use_simple_render = Bool(True)
    spot_size = Int(8)
    spot_color = Color('yellow')


    def __init__(self, x, y, *args, **kw):
        super(Indicator, self).__init__(x, y, *args, **kw)
        # print self.x, self.offset_x
        # self.x=x=self.x+self.offset_x
        # self.y=y=self.y+self.offset_y

        w = self.hline_length
        self.hline = Line(Point(x - w, y, **kw),
                          Point(x + w, y, **kw), **kw)
        h = self.vline_length
        self.vline = Line(Point(x, y - h, **kw),
                          Point(x, y + h, **kw), **kw)

        # self.primitives.append(self.hline)
        # self.primitives.append(self.vline)

    def _render_(self, gc, *args, **kw):
        with gc:
            if self.spot_color:
                sc = self._convert_color(self.spot_color)
                gc.set_fill_color(sc)
                gc.set_stroke_color(sc)

            x, y = self.get_xy()
            # if self.use_simple_render:
            # render a simple square at the current location
            # gc = args[0]
            l = self.spot_size
            hl = l / 2.
            x, y = x - hl, y - hl

            gc.rect(x, y, l, l)
            gc.draw_path()

            # else:
            # l = self.spot_size
            #
            # hl = l / 4.
            # x, y = x - hl, y - hl
            #
            #    gc.rect(x, y, l/2., l/2.)
            #    gc.draw_path()
            #    self.hline.render(*args, **kw)
            #    self.vline.render(*args, **kw)


# def set_canvas(self, canvas):
# super(Indicator, self).set_canvas(canvas)
# self.hline.set_canvas(canvas)
# self.vline.set_canvas(canvas)

class PointIndicator(Indicator):
    radius = 8
    # active = Bool(False)
    label_item = Any
    show_label = Bool(True)
    font = Str('modern 8')

    def __init__(self, x, y, *args, **kw):
        super(PointIndicator, self).__init__(x, y, *args, **kw)

        if self.identifier:
            self.label_item = Label(self.x, self.y,
                                    text=self.identifier,
                                    visible=self.identifier_visible,
                                    font=self.font,
                                    *args, **kw)
            self.primitives.append(self.label_item)

    def set_state(self, state):
        self.state = state

    def is_in(self, sx, sy):
        x, y = self.get_xy()
        if ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5 < self.radius:
            return True

    def adjust(self, dx, dy):
        super(PointIndicator, self).adjust(dx, dy)
        self.label.adjust(dx, dy)

    def _render_(self, gc, *args, **kw):
        super(PointIndicator, self)._render_(gc)

        if not self.use_simple_render:

            if self.label_item and self.show_label:
                self.label_item.render(gc)

            x, y = self.get_xy()

            if self.state:
                gc.rect(x - self.radius - 1,
                        y - self.radius - 1,
                        2 * self.radius + 1,
                        2 * self.radius + 1)

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
    # start_point=None
    def __init__(self, x, y, z=0, identifier='', **kw):
        super(PolyLine, self).__init__(x, y, **kw)
        # self.start_point=PointIndicator(x,y, **kw)
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

    # p1 = self.points[-1]
    # l = Line(p1, p2, default_color=line_color)
    #        self.primitives.append(l)
    #        self.lines.append(l)
    #
    #        self.points.append(p2)
    #        self.primitives.append(p2)

    def _render_(self, gc):
        for pi in self.primitives:
            pi.render(gc)


# self.start_point.render(gc)
# for pt in self.points:
# pt.render(gc)
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
    # clear_orientation = False
    clear_vorientation = False
    clear_horientation = False

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
    _cached_image = None
    _image_cache_valid = False
    scale = None

    def _render_(self, gc):
        if not self._image_cache_valid:
            self._compute_cached_image()

        if self._cached_image:
            x, y = self.get_xy()
            gc.translate_ctm(x, y)
            if self.scale:
                gc.scale_ctm(*self.scale)

            gc.draw_image(self._cached_image, rect=(0, 0, self.canvas.width, self.canvas.height))

    def _compute_cached_image(self):
        pic = PImage.open(self.path)
        data = array(pic)
        if not data.flags['C_CONTIGUOUS']:
            data = data.copy()

        if data.shape[2] == 3:
            kiva_depth = 'rgb24'
        elif data.shape[2] == 4:
            kiva_depth = 'rgba32'
        else:
            raise RuntimeError('Unknown colormap depth value: {}'.format(data.value_depth))

        self._cached_image = GraphicsContextArray(data, pix_format=kiva_depth)
        self._image_cache_valid = True


class Animation(object):
    cnt = 0
    tol = 0.05
    _last_refresh = None
    _animate = False
    cnt_tol = 360

    def toggle_animate(self):
        self._animate = not self._animate
        self.cnt = 0

    @property
    def animate(self):
        return self._animate and self.refresh_required()

    @animate.setter
    def set_animate(self, v):
        self._animate = v

    def reset_cnt(self):
        self.cnt = 0

    def increment_cnt(self, inc=1):
        self.cnt += inc
        if self.cnt >= self.cnt_tol:
            self.cnt -= self.cnt_tol

    def refresh_required(self):
        if not self._last_refresh or time.time() - self._last_refresh > self.tol:
            self._last_refresh = time.time()
            return True

# ============= EOF ====================================
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
