# ===============================================================================
# Copyright 2014 Jake Ross
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
from chaco.abstract_overlay import AbstractOverlay
from chaco.label import Label
from enable.base_tool import BaseTool
from enable.colors import ColorTrait
from kiva import FILL
from traits.api import List, Str, HasTraits, Float, Bool, Event, on_trait_change
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.time_series_graph import TimeSeriesStreamGraph

# class PositionAwareAction(Action):
# def perform(self, event):
#         if self.on_perform is not None:
#             self.on_perform(event.x, event.y)
#         return

class MarkerLabel(Label):
    rotate_angle = 0

    zero_y = 0
    xoffset = 10
    indicator_width = 4
    indicator_height = 10
    visible = Bool(True)
    component_height = 100

    def draw(self, gc, component_height):
        if not self.text:
            self.text = '     '

        if self.bgcolor != "transparent":
            gc.set_fill_color(self.bgcolor_)

        #draw tag border
        ox = self.x + self.xoffset
        with gc:
            gc.translate_ctm(ox, self.y)
            self._draw_tag_border(gc)
            super(MarkerLabel, self).draw(gc)

        with gc:
            gc.translate_ctm(self.x - self.indicator_width / 2.0, self.zero_y)
            self._draw_index_indicator(gc, component_height)

    def _draw_index_indicator(self, gc, component_height):
        # gc.set_fill_color((1, 0, 0, 1))
        w, h = self.indicator_width, self.indicator_height
        gc.draw_rect((0, 0, w, h), FILL)

        gc.draw_rect((0, component_height, w, h), FILL)

    def _draw_tag_border(self, gc):
        gc.set_stroke_color((0, 0, 0, 1))
        gc.set_line_width(2)

        # gc.set_fill_color((1, 1, 1, 1))
        bb_width, bb_height = self.get_bounding_box(gc)

        offset = 2
        xoffset = self.xoffset
        gc.lines([(-xoffset, (bb_height + offset) / 2.0),
                  (0, bb_height + 2 * offset),
                  (bb_width + offset, bb_height + 2 * offset),
                  (bb_width + offset, -offset),
                  (0, -offset),
                  (-xoffset, (bb_height + offset) / 2.0)])

        gc.draw_path()


class MarkerLine(HasTraits):
    x = Float
    height = Float
    visible = True
    bgcolor = ColorTrait

    def draw(self, gc, height):
        with gc:
            gc.set_stroke_color((0, 0, 0, 1))
            gc.move_to(self.x, 0)
            gc.line_to(self.x, height)
            gc.stroke_path()

    def set_visible(self, new):
        print 'set visible', new
        self.visible = new


class MarkerTool(BaseTool):
    overlay = None
    underlay = None
    text = ''

    marker_added = Event

    def normal_left_dclick(self, event):
        m = self.overlay.add_marker(event.x, event.y, self.text)
        l = self.underlay.add_marker_line(event.x)
        m.on_trait_change(l.set_visible, 'visible')
        self.component.invalidate_and_redraw()
        self.marker_added = m


class MarkerLineOverlay(AbstractOverlay):
    _cached_lines = List

    def add_marker_line(self, x, bgcolor='black'):
        l = MarkerLine(data_x=self.component.index_mapper.map_data(x),
                       x=x,
                       bgcolor=bgcolor)
        self._cached_lines.append(l)
        self._layout_needed = True
        return l

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.set_stroke_color((1, 0, 0, 0.75))
            gc.set_line_dash((12, 6))
            gc.translate_ctm(0, other_component.y)
            for l in self._cached_lines:
                if l.visible:
                    l.draw(gc, other_component.height)

    def _do_layout(self):
        if self._layout_needed:
            mapper = self.component.index_mapper
            for ci in self._cached_lines:
                if ci.visible:
                    ci.x = mapper.map_screen(ci.data_x)
                    ci.height = self.component.height
                    ci.visible = bool(ci.x > 0)

            self._layout_needed = False


class MarkerOverlay(AbstractOverlay):
    _cached_labels = List
    indicator_height = 10

    @on_trait_change('_cached_labels:[text, visible]')
    def _handle_text_change(self):
        self.request_redraw()

    def add_marker(self, x, y, text, bgcolor='white'):
        m = MarkerLabel(data_x=self.component.index_mapper.map_data(x),
                        indicator_height=self.indicator_height,
                        zero_y=self.component.y - self.indicator_height / 2.0,
                        bgcolor=bgcolor,
                        x=x,
                        y=y, text=text)
        self._cached_labels.append(m)
        self._layout_needed = True
        return m

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(other_component.x, other_component.y - self.indicator_height / 2.0,
                            other_component.width, other_component.height + self.indicator_height)

            # self._load_cached_labels()
            self._draw_labels(gc)

    def _do_layout(self):
        if self._layout_needed:
            mapper = self.component.index_mapper
            for ci in self._cached_labels:
                if ci.visible:
                    ci.x = mapper.map_screen(ci.data_x)
                    ci.visible = bool(ci.x > 0)
                    # print ci.data_x, ci.x, mapper.range.low, mapper.range.high
            self._layout_needed = False

    def _draw_labels(self, gc):
        for ci in self._cached_labels:
            if ci.visible:
                with gc:
                    ci.draw(gc, self.component.height)


class SpectrometerScanGraph(TimeSeriesStreamGraph):
    marker_text = Str
    visual_marker_counter = 0
    markers = List

    def _x_limits_changed_changed(self):
        self.invalidate_markers()

    def invalidate_markers(self):
        for o in self.get_marker_overlays():
            o._layout_needed = True
            o.do_layout()

    def get_marker_overlays(self):
        return [o for p in self.plots
                for o in p.overlays if isinstance(o, MarkerOverlay)]

    def add_visual_marker(self, text=None, bgcolor='white'):
        if text is None:
            text = self.marker_text

        for i, p in enumerate(self.plots):
            for t in p.overlays:
                if isinstance(t, MarkerOverlay):
                    xd = p.data.get_data('x1')
                    x = p.map_screen([(xd[-1], 0)])[0][0]
                    y = 500 + self.visual_marker_counter * 21
                    if y > p.y2 - 20:
                        self.visual_marker_counter = -1
                        y = p.y2 - 20

                    m = t.add_marker(x, y, text, bgcolor)
                    self.visual_marker_counter += 1
                    self.markers.append(m)
                    for u in p.underlays:
                        if isinstance(u, MarkerLineOverlay):
                            l = u.add_marker_line(x, bgcolor)
                            m.on_trait_change(l.set_visible, 'visible')
        self.redraw()

    def new_plot(self, *args, **kw):
        p = super(SpectrometerScanGraph, self).new_plot(*args, **kw)

        mo = MarkerOverlay(component=p)
        mu = MarkerLineOverlay(component=p)

        mt = MarkerTool(component=p, overlay=mo, underlay=mu)
        mt.on_trait_change(self._update_markers, 'marker_added')

        p.tools.append(mt)
        p.overlays.append(mo)
        p.underlays.append(mu)

        return p

    def _marker_text_changed(self, new):
        for p in self.plots:
            for t in p.tools:
                if isinstance(t, MarkerTool):
                    t.text = new

                    # def add_marker(self, x, y):
                    #     print x, y

    def _update_markers(self, new):
        self.markers.append(new)


    @on_trait_change('markers[]')
    def _handle_markers_change(self, obj, name, old, new):
        if len(new)<len(old):
            for p in self.plots:
                un = None
                for u in p.underlays:
                    if isinstance(u,MarkerLineOverlay):
                        un=u
                        break

                for i, o in enumerate(p.overlays):
                    if isinstance(o, MarkerOverlay):
                        for j, ci in enumerate(o._cached_labels):
                            if ci not in new:
                                o._cached_labels.pop(j)
                                if un:
                                    un._cached_lines.pop(j)


#============= EOF =============================================



