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
from chaco.array_data_source import ArrayDataSource
from chaco.data_range_1d import DataRange1D
from chaco.linear_mapper import LinearMapper
from chaco.lineplot import LinePlot
from chaco.plot_containers import OverlayPlotContainer
from chaco.scatterplot import ScatterPlot
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
from numpy import linspace
# ============= local library imports  ==========================
from pychron.processing.plotters.base_inset import BaseInset


class InverseIsochronLineInset(BaseInset, LinePlot):
    def __init__(self, *args, **kw):
        self.border_visible = kw.get('border_visible', True)
        BaseInset.__init__(self, *args, **kw)
        LinePlot.__init__(self)

        if not self.visible_axes:
            self.x_axis.visible = False
            self.y_axis.visible = False


class InverseIsochronPointsInset(BaseInset, ScatterPlot):
    nominal_intercept = Float

    def __init__(self, *args, **kw):
        ScatterPlot.__init__(self)
        BaseInset.__init__(self, *args, **kw)

        self.border_visible = kw.get('border_visible', True)
        self.marker = 'circle'
        # self.color = 'red'
        # self.marker_size = 1.5
        if not self.visible_axes:
            self.x_axis.visible = False
            self.y_axis.visible = False

    def overlay(self, component, gc, *args, **kw):
        super(InverseIsochronPointsInset, self).overlay(component, gc, *args, **kw)
        self._draw_atm(gc)
        self._draw_zero(gc)

    def _draw_zero(self, gc):
        with gc:
            yl, yh = self.value_range.low, self.value_range.high
            pts = self.map_screen([(0, yl), (0, yh)])
            gc.set_line_dash((3, 5))
            gc.lines(pts)
            gc.draw_path()

    def _draw_atm(self, gc):
        with gc:
            xl = self.index_range.low
            pts = self.map_screen([(xl, self.nominal_intercept), (0, self.nominal_intercept)])

            # print x,y
            # gc.move_to(0,y)
            # gc.line_to(x,y)
            gc.set_line_width(1.25)
            gc.lines(pts)
            gc.draw_path()


            # reg = self.regressor
            # xintercept = reg.x_intercept * 1.1
            # yintercept = reg.predict(0)

            # m, _ = self.index.get_bounds()
            # self.index_range.low = lx = -0.1 * (xintercept - m)
            # self.index_range.high = hx = xintercept
            #
            # self.value_range.low = 0
            # self.value_range.high = max(1 / 300., yintercept * 1.1)

            # xs = linspace(lx, hx, 20)
            # ys = reg.predict(xs)
            # print 'xs', xs.shape
            # print 'ys', ys.shape
            #
            # index = ArrayDataSource(xs)
            # value = ArrayDataSource(ys)
            # index_range = DataRange1D()
            # index_range.add(index)
            # index_mapper = LinearMapper(range=index_range)
            # index_range.tight_bounds = False
            #
            # value_range = DataRange1D()
            # value_range.add(value)
            # value_mapper = LinearMapper(range=value_range)
            # value_range.tight_bounds = False
            #
            # lp = ScatterPlot()
            # lp.index = index
            # lp.value = value
            # lp.index_mapper = index_mapper
            # lp.value_mapper = value_mapper

            # self.underlays.append(lp)
            # self.plots.append(lp)

            # print self.get_screen_points()
            # print lp.get_screen_points()

            # ============= EOF =============================================



