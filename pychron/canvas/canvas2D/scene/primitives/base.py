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
from kiva.fonttools import str_to_font
from pyface.ui_traits import PyfaceColor
from traits.api import (
    HasTraits,
    Str,
    Any,
    Float,
    Property,
    on_trait_change,
    List,
)
from traitsui.api import View, Item, VGroup, HGroup


# ============= standard library imports ========================
# ============= local library imports  ==========================


class Primitive(HasTraits):
    identifier = Str
    identifier_visible = True
    type_tag = Str
    scene_visible = True

    x = Float
    y = Float
    ox = Float
    oy = Float
    offset_x = Float
    offset_y = Float
    force_layout = False

    state = False
    selected = False

    default_color = PyfaceColor("red")
    active_color = PyfaceColor("green")
    selected_color = PyfaceColor("blue")
    name_color = PyfaceColor("black")
    text_color = PyfaceColor("black")

    canvas = Any

    line_width = 1

    name = Str
    name_visible = True
    name_offsetx = 0
    name_offsety = 0

    klass_name = Property

    space = "data"
    visible = True

    primitives = List
    font = Str("modern 14")

    width = Float
    height = Float
    _initialized = False

    _cached_wh = None
    _cached_xy = None
    _layout_needed = True
    _cached_colors = None
    _cached_text_extent = None
    _cached_bounds = None
    _cached_bounds_key = None

    def __init__(self, x, y, *args, **kw):
        self.x = x
        self.y = y
        self.ox = x
        self.oy = y
        self._cached_colors = {}
        self._cached_text_extent = {}
        self._cached_bounds = None
        self._cached_bounds_key = None
        super(Primitive, self).__init__(*args, **kw)
        self._initialized = True

    def toyaml(self):
        return {
            "name": self.name,
            "translation": "{:0.2f},{:0.2f}".format(self.x, self.y),
            "dimension": "{:0.2f}, {:0.2f}".format(self.width, self.height),
        }

    def edit_view(self):
        v = View(
            VGroup(
                Item("name"),
                HGroup(Item("x"), Item("y")),
                HGroup(Item("width"), Item("height")),
            )
        )
        return v

    @property
    def gfont(self):
        return str_to_font(self.font)

    @property
    def label(self):
        return "{} {} {}".format(self.klass_name, self.name, self.identifier)

    def request_layout(self):
        self._cached_wh = None
        self._cached_xy = None
        self._cached_bounds = None
        self._layout_needed = True

    def render(self, gc):
        with gc:
            if self.visible:
                self.set_stroke_color(gc)
                self.set_fill_color(gc)

                gc.set_font(self.gfont)
                gc.set_line_width(self.line_width)

                self._render(gc)

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

    def adjust(self, dx, dy):
        args = self.canvas.map_data((dx, dy))
        aargs = self.canvas.map_data((0, 0))
        dx = args[0] - aargs[0]
        dy = args[1] - aargs[1]
        self.x += dx
        self.y += dy

    def get_xy(self, x=None, y=None, clear_layout_needed=True, force=False):
        if force or self._layout_needed or not self._cached_xy:
            if x is None:
                x = self.x
            if y is None:
                y = self.y
            # x, y = self.x, self.y
            offset = 0
            if self.space == "data":
                # if self.canvas is None:
                # print self
                if self.canvas:
                    x, y = self.canvas.map_screen([(x, y)])[0]
                    # offset = self.canvas.offset
                    offset = 1
                    x += self.offset_x
                    y += self.offset_y

            rx, ry = x + offset, y + offset
            if clear_layout_needed:
                self._layout_needed = False
        else:
            rx, ry = self._cached_xy
        self._cached_xy = rx, ry

        return rx, ry

    def get_wh(self):
        w, h = 0, 0
        if self.canvas:
            if self._layout_needed or not self._cached_wh:
                w, h = self.width, self.height
                # w, h = 20, 20
                if self.space == "data":
                    (w, h), (ox, oy) = self.canvas.map_screen(
                        [(self.width, self.height), (0, 0)]
                    )
                    w, h = w - ox, h - oy
            else:
                w, h = self._cached_wh
            self._cached_wh = w, h

        return w, h

    def map_dimension(self, d, keep_square=False):
        (w, h), (ox, oy) = self.canvas.map_screen([(d, d), (0, 0)])
        w, h = w - ox, h - oy
        if keep_square:
            w = min(w, h)

        return w

    def get_bounds(self):
        """Get bounding box as (x, y, x2, y2)."""
        canvas_bounds = None
        if self.canvas is not None:
            canvas_bounds = tuple(self.canvas.bounds) if self.canvas.bounds is not None else None
            if self.bounds != canvas_bounds:
                self._layout_needed = True
                self.bounds = canvas_bounds

        key = (self.x, self.y, self.width, self.height, canvas_bounds)
        if self._cached_bounds is None or self._cached_bounds_key != key:
            x, y = self.get_xy(clear_layout_needed=False)
            w, h = self.get_wh()
            self._cached_bounds = (x, y, x + w, y + h)
            self._cached_bounds_key = key
        return self._cached_bounds

    bounds = None

    def set_canvas(self, canvas):
        if canvas:
            self._layout_needed = canvas != self.canvas or self.bounds != canvas.bounds

        if self.force_layout:
            self._layout_needed = True
            self.force_layout = False

        self.canvas = canvas
        if canvas:
            self.bounds = canvas.bounds
        else:
            self.bounds = None

        for pi in self.primitives:
            pi.set_canvas(canvas)

    def set_state(self, state):
        self.state = state

    def set_selected(self, selected):
        self.selected = selected

    def is_in_region(self, x1, x2, y1, y2):
        """
        Check if component's bounding box intersects with region.

          x1,y1 ---------------
          |                   |
          |    component      |
          |        (x,y)     |
          |        +----+     |
          |        |    |     |
          |        +----+-----|
          |              (x2,y2)

        Returns True if component intersects region.
        """
        bx, by, bx2, by2 = self.get_bounds()

        return not (x2 < bx or x1 > bx2 or y2 < by or y1 > by2)

    # private
    def _render(self, gc):
        pass

    def _render_name(self, gc, x, y, w, h):
        if self.name and self.name_visible:
            with gc:
                # c = self.text_color if self.text_color else self.default_color
                gc.set_fill_color(self._convert_color(self.name_color))
                txt = str(self.name)
                self._render_textbox(gc, x, y, w, h, txt)

    def _render_textbox(self, gc, x, y, w, h, txt):
        if txt not in self._cached_text_extent:
            tw, th, _, _ = gc.get_full_text_extent(txt)
            self._cached_text_extent[txt] = (tw, th)
        else:
            tw, th = self._cached_text_extent[txt]
        x = x + w / 2.0 - tw / 2.0
        y = y + h / 2.0 - th / 2.0

        self._render_text(gc, txt, x, y)

    def _render_text(self, gc, t, x, y):
        with gc:
            gc.translate_ctm(x, y)
            gc.set_fill_color(self._convert_color(self.text_color))
            gc.set_text_position(0, 0)
            gc.show_text(t)

    def _convert_color(self, c):
        cache_key = id(c)
        if cache_key in self._cached_colors:
            return self._cached_colors[cache_key]

        if not isinstance(c, (list, tuple)):
            c = c.red, c.green, c.blue
        c = [x / 255.0 for x in c]

        self._cached_colors[cache_key] = c
        return c

    # handlers
    @on_trait_change(
        "default_color, active_color, name_color, text_color, x, y, width, height, state, visible"
    )
    def _refresh_canvas(self):
        self._cached_colors.clear()
        self._cached_text_extent.clear()
        self._cached_bounds = None
        self.request_redraw()

    def request_redraw(self):
        if self.canvas:
            self.canvas.request_redraw()

    def _get_klass_name(self):
        return self.__class__.__name__


class QPrimitive(Primitive):
    def _convert_color(self, c):
        cache_key = id(c)
        if cache_key in self._cached_colors:
            return self._cached_colors[cache_key]

        if not isinstance(c, (list, tuple)):
            c = c.rgba

        if any((ci > 1 for ci in c)):
            c = [x / 255.0 for x in c]

        self._cached_colors[cache_key] = c
        return c

    def is_in(self, x, y):
        mx, my = self.get_xy()
        w, h = self.get_wh()
        return mx <= x <= (mx + w) and my <= y <= (my + h)


class Connectable(QPrimitive):
    connections = List
    volume = Float

    @on_trait_change("x,y")
    def _update_xy(self):
        if not self._initialized:
            return

        # cvo = self.x != self.ox
        # cho = self.y != self.oy
        w, h = self.width, self.height
        for t, c in self.connections:
            # c.clear_vorientation = cvo
            # c.clear_horientation = cho

            func = getattr(c, "set_{}point".format(t))
            func((self.x + w / 2.0, self.y + h / 2.0))
            c.request_layout()

        self.request_redraw()


# ============= EOF =============================================
