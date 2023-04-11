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

# ============= standard library imports ========================
from numpy import array

# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev

# from pychron.processing.plotters.xy.xy_scatter_tool import XYScatterTool
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure


class XYScatter(BaseArArFigure):
    def build(self, plots, *args, **kwargs):
        graph = self.graph
        opt = self.options
        padding = opt.get_paddings()
        for i, po in enumerate(plots):
            p = graph.new_plot(ytitle=po.ytitle, xtitle=po.xtitle, padding=padding)
            self._setup_plot(i, p, po)

        graph.refresh()

    def plot(self, plots, legend=None):
        graph = self.graph
        opt = self.options
        if plots:
            for i, po in enumerate(plots):
                if po.name in ("Ratio", "Scatter"):
                    self._plot_ratio(po, i)
                elif po.name == "TimeSeries":
                    self._plot_series(po, i)

                if opt.show_statistics:
                    graph.add_statistics(plotid=i)

    def _plot_ratio(self, po, i):
        xs = [nominal_value(ai) for ai in self._unpack_attr(po.xtitle)]
        ys = [nominal_value(ai) for ai in self._unpack_attr(po.ytitle)]

        plot, scatter, line = self.graph.new_series(
            x=array(xs),
            y=array(ys),
            fit=po.fit,
            add_inspector=False,
            marker=po.marker,
            marker_size=po.marker_size,
        )

        opt = self.options
        nsigma = opt.error_bar_nsigma
        for axk in "xy":
            caps = getattr(opt, "{}_end_caps".format(axk))
            visible = getattr(po, "{}_error".format(axk))

            attr = getattr(po, "{}title".format(axk))
            es = [std_dev(ai) for ai in self._unpack_attr(attr)]
            self._add_error_bars(
                scatter, es, axk, nsigma, end_caps=caps, visible=visible
            )

    def _plot_series(self, po, i):
        pass


# ============= EOF =============================================
