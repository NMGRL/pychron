# ===============================================================================
# Copyright 2014 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from chaco.array_data_source import ArrayDataSource
from chaco.axis import PlotAxis
from chaco.data_range_1d import DataRange1D
from chaco.linear_mapper import LinearMapper
from chaco.lineplot import LinePlot
from traits.api import Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
GOLDEN_RATIO = 1.618


class IdeogramInset(LinePlot):
    location = Str
    border_visible = True

    def __init__(self, xs, ys, index_bounds=None, value_bounds=None, *args, **kw):

        index = ArrayDataSource(xs)
        value = ArrayDataSource(ys)
        if index_bounds is not None:
            index_range = DataRange1D(low=index_bounds[0], high=index_bounds[1])
        else:
            index_range = DataRange1D()
        index_range.add(index)
        index_mapper = LinearMapper(range=index_range)

        if value_bounds is not None:
            value_range = DataRange1D(low=value_bounds[0], high=value_bounds[1])
        else:
            value_range = DataRange1D()
        value_range.add(value)
        value_mapper = LinearMapper(range=value_range)

        self.index = index
        self.value = value
        self.index_mapper = index_mapper
        self.value_mapper = value_mapper
        # self.color = "red"
        # self.line_width = 1.0
        # self.line_style = "solid"

        left = PlotAxis(orientation='left', mapper=value_mapper,
                        tick_label_formatter=lambda x: '',
                        tick_visible=False)

        bottom = PlotAxis(orientation='bottom',
                          mapper=index_mapper,
                          tick_label_font='modern 8')
        self.underlays.append(left)
        self.underlays.append(bottom)

        super(IdeogramInset, self).__init__(*args, **kw)

    def _compute_location(self, component):
        x1, y1 = component.x, component.y
        x2, y2 = component.x2, component.y2
        w = self.width
        h = self.height
        # w = h * GOLDEN_RATIO
        loc = self.location
        if 'Upper' in loc:
            y = y2 - h - 2
        else:
            y = y1 + 2
        if 'Right' in loc:
            x = x2 - w - 2
        else:
            x = x1 + 2

        self.x, self.y, self.width, self.height = x, y, w, h
        # print self.x, self.y, self.width, self.height

    def overlay(self, component, gc, *args, **kw):
        with gc:
            gc.clip_to_rect(component.x, component.y, component.width, component.height)
            self._compute_location(component)
            self._draw_underlay(gc, *args, **kw)
            self._draw_plot(gc, *args, **kw)
            self._draw_border(gc, *args, **kw)

# ============= EOF =============================================

