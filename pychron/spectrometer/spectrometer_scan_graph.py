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
from kiva import FILL
from traits.api import List, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.graph.time_series_graph import TimeSeriesStreamGraph

# class PositionAwareAction(Action):
#     def perform(self, event):
#         if self.on_perform is not None:
#             self.on_perform(event.x, event.y)
#         return

class MarkerLabel(Label):
    rotate_angle = 0

    zero_y=45
    xoffset = 10
    indicator_width=10
    def draw(self, gc):

        #draw tag border
        with gc:
            gc.translate_ctm(self.x, self.y)
            self._draw_tag_border(gc)
            super(MarkerLabel, self).draw(gc)

        with gc:
            gc.translate_ctm(self.x-self.xoffset-self.indicator_width/2.0, self.zero_y)
            self._draw_index_indicator(gc)

    def _draw_index_indicator(self, gc):
        gc.set_fill_color((1,0,0,1))
        # gc.rect(0,0, 10, 10)
        width,height=10,10
        gc.draw_rect((0, 0, width, height), FILL)

    def _draw_tag_border(self, gc):

        gc.set_stroke_color((0,0,0,1))
        gc.set_line_width(2)
        gc.set_fill_color((1,1,1,1))
        bb_width, bb_height = self.get_bounding_box(gc)

        offset = 2
        xoffset = self.xoffset
        gc.lines([(-xoffset,(bb_height+offset)/2.0),
        (0, bb_height+offset),
        (bb_width+offset, bb_height+offset),
        (bb_width+offset, -offset),
        (0,-offset),
        (-xoffset,(bb_height+offset)/2.0)])

        gc.draw_path()


class MarkerTool(BaseTool):
    overlay = None
    text = ''
    def normal_left_dclick(self, event):
        self.overlay.add_marker(event.x,event.y, self.text)

class MarkerOverlay(AbstractOverlay):
    _cached_labels = List

    def add_marker(self, x, y, text):
        # x=self.component.x+x
        self._cached_labels.append(MarkerLabel(x=x+10, y=y, text=text))

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            # self._load_cached_labels()
            self._draw_labels(gc)

    # def _load_cached_labels(self):
    #     if self._layout_needed or not self._cached_labels:
    #         self._cached_labels=self._cached_labels

    def _draw_labels(self, gc):
        for ci in self._cached_labels:
            with gc:
                ci.draw(gc)


class SpectrometerScanGraph(TimeSeriesStreamGraph):
    # def get_child_context_menu_actions(self):
    #     return [PositionAwareAction(name='Add marker',
    #                                 on_perform =self.add_marker)]
    marker_text = Str
    visual_marker_counter = 0

    def add_visual_marker(self):
        for i,p in enumerate(self.plots):
            for t in p.overlays:
                if isinstance(t, MarkerOverlay):
                    xd = p.data.get_data('x1')
                    x=p.map_screen([(xd[-1],0)])[0][0]
                    y=500+self.visual_marker_counter*50
                    if y>p.y2-20:
                        self.visual_marker_counter=-1
                        y = p.y2-20

                    t.add_marker(x,y,self.marker_text)
                    self.visual_marker_counter+=1

    def new_plot(self, *args, **kw):
        p = super(SpectrometerScanGraph, self).new_plot(*args, **kw)

        mo = MarkerOverlay(component=p)
        mt = MarkerTool(component=p, overlay=mo)
        # self._marker_overlays.append(mo)
        p.tools.append(mt)
        p.overlays.append(mo)

        return p

    def _marker_text_changed(self, new):
        for p in self.plots:
            for t in p.tools:
                if isinstance(t, MarkerTool):
                    t.text=new

    # def add_marker(self, x, y):
    #     print x, y
#============= EOF =============================================



