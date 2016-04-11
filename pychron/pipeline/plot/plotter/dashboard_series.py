# ===============================================================================
# Copyright 2013 Jake Ross
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
from chaco.scales.time_scale import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from numpy import Inf
from traits.api import Array, Dict

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure

N = 500


class DashboardSeries(BaseArArFigure):
    xs = Array
    measurements = Dict

    def build(self, plots):
        graph = self.graph
        for po in plots:
            if po.use:
                p = graph.new_plot(padding=self.padding,
                                   ytitle=po.name,
                                   xtitle='Time')

                p.value_scale = po.scale
                p.padding_left = 75
                p.value_range.tight_bounds = False

    def plot(self, plots, legend=None):
        """
            plot data on plots
        """
        graph = self.graph

        if plots:
            # px = plots[0]
            #            data = self.measurements[px.name]
            #            if data is None:
            #                return
            _mi, _ma = Inf, -Inf
            with graph.no_regression(refresh=True):
                plots = [po for po in plots if po.use]

                for i, po in enumerate(plots):
                    xs, ys = [], []
                    data = self.measurements[po.name]
                    if data is not None:
                        xs, ys = data.T
                        _mi = min(min(xs), _mi)
                        _ma = max(max(xs), _ma)
                        if not po.use_time_axis:
                            xs /= 3600
                        else:
                            graph.convert_index_func = lambda x: '{:0.2f} hrs'.format(x / 3600.)

                    self._plot_series(po, i, xs, ys)

                if plots:
                    window_hours = 6
                    _ma = max(_ma, _mi + 3600 * window_hours)
                    graph.set_x_limits(min_=_mi, max_=_ma, pad='0.1',
                                       plotid=0)

    def _plot_series(self, po, pid, xs, ys):
        graph = self.graph
        try:
            scatter, p = graph.new_series(x=xs,
                                          y=ys,
                                          fit=po.fit,
                                          plotid=pid,
                                          type='scatter')
            if po.use_time_axis:
                p.x_axis.tick_generator = ScalesTickGenerator(scale=CalendarScaleSystem())

        except (KeyError, ZeroDivisionError), e:
            print 'Series', e

# ===============================================================================
# plotters
# ===============================================================================

# ===============================================================================
# overlays
# ===============================================================================

# ===============================================================================
# utils
# ===============================================================================

# ===============================================================================
# labels
# ===============================================================================

# ============= EOF =============================================
