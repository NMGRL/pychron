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
import math

from chaco.axis import PlotAxis
from enable.component_editor import ComponentEditor
from enable.label import Label
from traits.api import HasTraits, Str
from traitsui.api import View, UItem

# ============= standard library imports ========================
from numpy import array, float64
# ============= local library imports  ==========================

# http://stackoverflow.com/questions/2358890/python-lexical-analysis-and-tokenization
# http://effbot.org/zone/xml-scanner.htm

import re

xml = re.compile(r"""
    <([/?!]?\w+)     # 1. tags
    |&(\#?\w+);      # 2. entities
    |([^<>&'\"=\s]+) # 3. text strings (no special characters)
    |(\s+)           # 4. whitespace
    |(.)             # 5. special characters
    """, re.VERBOSE)


def tokenize(text):
    scan = xml.scanner(text)
    while 1:
        m = scan.match()
        if not m:
            break
        tok = m.group(m.lastindex)
        if tok != '>':
            yield tok


def clean(text):
    t = ''.join((ti for ti in tokenize(text) if ti not in ('sup', '/sup', 'sub', '/sub')))
    return t


class MPlotAxis(PlotAxis):
    def clone(self, ax):
        for attr in ('mapper', 'origin',
                     'title_font',
                     'title_spacing',
                     'title_color',
                     'tick_weight',
                     'tick_color',
                     'tick_label_font',
                     'tick_label_color',
                     'tick_label_rotate_angle',
                     'tick_label_alignment',
                     'tick_label_margin',
                     'tick_label_offset',
                     'tick_label_position',
                     'tick_label_formatter',
                     'tick_in',
                     'tick_out',
                     'tick_visible',
                     'tick_interval',
                     'tick_generator',
                     'orientation',
                     'axis_line_visible',
                     'axis_line_color',
                     'axis_line_weight',
                     'axis_line_style',
                     'small_haxis_style',
                     'ensure_labels_bounded',
                     'ensure_ticks_bounded',
                     'bgcolor',
                     'resizable',
                     'tag'):
            try:
                setattr(self, attr, getattr(ax, attr))
            except AttributeError:
                pass

    def _draw_title(self, gc, label=None, axis_offset=None):
        if label is None:
            title_label = MLLabel(text=self.title,
                                  font=self.title_font,
                                  color=self.title_color,
                                  rotate_angle=self.title_angle,
                                  orientation=self.orientation)
        else:
            title_label = label

        # get the _rotated_ bounding box of the label
        tl_bounds = array(title_label.get_bounding_box(gc), float64)
        text_center_to_corner = -tl_bounds / 2.0
        # which axis are we moving away from the axis line along?
        axis_index = self._major_axis.argmin()

        if self.title_spacing != 'auto':
            axis_offset = self.title_spacing

        if (self.title_spacing) and (axis_offset is None ):
            if not self.ticklabel_cache:
                axis_offset = 25
            else:
                axis_offset = max([l._bounding_box[axis_index] for l in self.ticklabel_cache]) * 1.3

        offset = (self._origin_point + self._end_axis_point) / 2
        axis_dist = self.tick_out + tl_bounds[axis_index] / 2.0 + axis_offset
        offset -= self._inside_vector * axis_dist
        offset += text_center_to_corner

        gc.translate_ctm(*offset)
        title_label.draw(gc)
        gc.translate_ctm(*(-offset))
        return


class MLLabel(Label):
    _text_positions = None
    mltext = Str
    _cached_text_width = None

    def _text_changed(self, t):
        self._cached_text_width = None

        self.mltext = t
        self.trait_setq(text=clean(t))
        self._calculate_text_positions()

    def _calculate_text_positions(self):
        texts = []
        offset = 0
        for ti in tokenize(self.mltext):
            if ti == 'sup':
                offset = 1
            elif ti == 'sub':
                offset = -1
            elif ti in ('/sup', '/sub'):
                offset = 0
            else:
                texts.append((offset, ti))
        self._text_positions = texts

    def _calculate_text_width(self, gc):
        ofont = self.font
        sfont = self.font.copy()
        sfont.size = int(sfont.size * 0.6)
        suph = int(ofont.size * 0.5)
        subh = -int(ofont.size * 0.3)

        s = 0
        mh = 0
        if self._cached_text_width is None:
            for offset, text in self._text_positions:
                with gc:
                    if offset == 1:
                        gc.translate_ctm(0, suph)
                        gc.set_font(sfont)
                    elif offset == -1:
                        gc.set_font(sfont)
                        gc.translate_ctm(0, subh)
                    else:
                        gc.set_font(ofont)

                    w, h, _, _ = gc.get_full_text_extent(text)
                    s += w

            self._cached_text_width = s

        return self._cached_text_width

    def _draw_mainlayer(self, gc, view_bounds=None, mode="normal"):
        self._calculate_text_width(gc)
        self._calc_line_positions(gc)
        with gc:
            gc.translate_ctm(*self.position)

            gc.set_font(self.font)
            gc.set_fill_color(self.color_)
            poss = self._text_positions
            if self.orientation in ('top', 'bottom'):
                self._draw_horizontal(gc, poss)
            else:
                self._draw_vertical(gc, poss)

    def _draw_vertical(self, gc, poss):
        bb = self._bounding_box
        gc.translate_ctm(bb[1]-2, 0)
        gc.rotate_ctm(math.radians(90))
        self._draw_horizontal(gc, poss)

    def _draw_horizontal(self, gc, poss):
        ofont = self.font
        sfont = self.font.copy()
        sfont.size = int(sfont.size * 0.6)
        suph = int(ofont.size * 0.5)
        subh = -int(ofont.size * 0.3)

        # need to correct for the difference between the enable.Label's calculated width and the actual
        # width. Label calculates the width without the markup so its greater than the real width.
        w = self._calculate_text_width(gc)
        ow = self._bounding_box[0]
        gc.translate_ctm((ow - w)/2, 0)

        x = 0
        for offset, text in poss:
            with gc:
                if offset == 1:
                    gc.translate_ctm(0, suph)
                    gc.set_font(sfont)
                elif offset == -1:
                    gc.set_font(sfont)
                    gc.translate_ctm(0, subh)
                else:
                    gc.set_font(ofont)

                w, h, _, _ = gc.get_full_text_extent(text)
                gc.set_text_position(x, 0)
                gc.show_text(text)
                x += w


class Demo(HasTraits):
    def traits_view(self):
        v = View(UItem('plot', editor=ComponentEditor()),
                 resizable=True)
        return v


if __name__ == '__main__':
    # m = MLLabel()
    # m.text = '<sup>40</sup>Ar'
    # d = Demo()
    # d.plot = Plot()
    # d.plot.padding_left = 80
    # d.plot.data = ArrayPlotData()
    # d.plot.data['x'] = [1, 2, 3, 4]
    # d.plot.data['y'] = [1, 2, 3, 4]
    # d.plot.plot(('x', 'y'))
    from pychron.graph.stacked_graph import StackedGraph

    g = StackedGraph()
    plot = g.new_plot(padding_left=100, padding_bottom=100)
    xa = plot.x_axis
    xa.title_color = 'red'
    xa.title = 'sasfas'
    nxa = MPlotAxis()
    nxa.title = '<sup>39</sup>Ar/<sup>40</sup>Ar'
    # nxa.title = '39Ar/40Ar'
    nxa.clone(xa)

    ya = plot.y_axis
    ya.title_color = 'red'
    ya.title = 'sasfas'
    ya.title_font = 'modern 36'
    nya = MPlotAxis()
    nya.title = '<sup>39</sup>Ar/<sup>40</sup>Ar'
    # nya.title = '39Ar/40Ar'
    nya.clone(ya)

    plot.x_axis = nxa
    plot.y_axis = nya

    plot = g.new_plot(padding_left=100, padding_bottom=100)
    plot.y_axis.title = 'Foo'
    plot.y_axis.title_font = 'modern 18'
    g.configure_traits()

# ============= EOF =============================================



