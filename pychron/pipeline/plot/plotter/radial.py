# ===============================================================================
# Copyright 2017 ross
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
from traits.api import Array
from chaco.abstract_overlay import AbstractOverlay
from uncertainties import std_dev, nominal_value
from numpy import array

from pychron.core.stats import calculate_weighted_mean
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure


class RadialOverlay(AbstractOverlay):
    xs = Array
    ys = Array

    def __init__(self, component, xs, ys, *args, **kw):
        super(RadialOverlay, self).__init__(component, *args, **kw)
        self._xs, self._ys = xs, ys

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        print self.component.datasources


class Radial(BaseArArFigure):
    def plot(self, plots, legend=None):
        graph = self.graph
        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            self._plot_radial(po, plotobj, pid)

    def post_make(self):
        g = self.graph
        for i, p in enumerate(g.plots):
            l, h = self.ymis[i], self.ymas[i]
            print i, p, l, h
            g.set_y_limits(l, h, pad='0.1', plotid=i)

    def _plot_radial(self, po, plot, pid):

        zs = array([nominal_value(a.uage) for a in self.analyses])
        es = array([std_dev(a.uage) for a in self.analyses])

        zm,_ = calculate_weighted_mean(zs, es)
        zs = (zs - zm)/es

        yma = max(abs(zs))
        es = 1/es
        # xs = array([1/std_dev(a.uage) for a in self.analyses])
        # ys = array([nominal_value(a.uage)/(std_dev(a.uage)) for a in self.analyses])
        try:
            self.ymis[pid] = min(self.ymis[pid], -yma)
            self.ymas[pid] = max(self.ymas[pid], yma)
        except IndexError:
            self.ymis.append(-yma)
            self.ymas.append(yma)
        # overlay = RadialOverlay(plot, xs=xs, ys=ys)
        # plot.overlays.append(overlay)
        s, _ = self.graph.new_series(es, zs, type='scatter')
        self._add_scatter_inspector(s)
        self.graph.set_x_limits(min_=0)
        # self.graph.set_y_limits(min_=-a, max_=a, pad='0.1')
# ============= EOF =============================================
