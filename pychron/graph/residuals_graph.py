# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from chaco.api import (
    PlotGrid,
    BarPlot,
    ArrayDataSource,
    DataRange1D,
    LinearMapper,
    add_default_axes,
)

# =============local library imports  ==========================
from chaco.axis import PlotAxis

from pychron.graph.graph import container_factory
from pychron.graph.guide_overlay import GuideOverlay
from pychron.graph.regression_graph import RegressionGraph


# =============standard library imports ========================


class ResidualsGraph(RegressionGraph):
    """ """

    xtitle = None

    def _plotcontainer_default(self):
        """ """
        return self.container_factory()

    def container_factory(self):
        """ """
        kw = {"type": "v", "stack_order": "top_to_bottom"}
        for k, v in self.container_dict.items():
            kw[k] = v
        return container_factory(**kw)

        # def _metadata_changed(self, obj, name, new):
        """
        """
        # super(ResidualsGraph, self)._metadata_changed(obj, name, new)
        # self.update_residuals()

    # def _update_graph(self, *args, **kw):
    #     super(ResidualsGraph, self)._update_graph(*args, **kw)
    #     self.update_residuals()
    #

    def _regression_results_changed(self, regs):
        super(ResidualsGraph, self)._regression_results_changed()
        reg = regs[0][1]

        res = reg.calculate_residuals()
        x = reg.clean_xs

        if x is not None:
            xn, rn, xp, rp = self._split_residual(x, res)

            nplot = self.residual_plots[0]
            pplot = self.residual_plots[1]

            nplot.index.set_data(xn)
            pplot.index.set_data(xp)

            nplot.value.set_data(rn)
            pplot.value.set_data(rp)

    def _split_residual(self, x, res):
        """ """
        neg = res <= 0
        pos = res > 0
        return x[neg], res[neg], x[pos], res[pos]

    # def add_datum(self, *args, **kw):
    #     """
    #     """
    #     super(ResidualsGraph, self).add_datum(*args, **kw)
    #     self.update_residuals()

    # def new_plot(self, *args, **kw):
    #     self.xtitle = kw['xtitle'] if 'xtitle' in kw else None
    #     return super(ResidualsGraph, self).new_plot(*args, **kw)

    def new_series(self, x=None, y=None, plotid=0, **kw):
        """ """

        plot, scatter, line = super(ResidualsGraph, self).new_series(
            x=x, y=y, plotid=plotid, **kw
        )
        # for underlay in plot.underlays:
        #     if underlay.orientation == 'bottom':
        #         underlay.visible = False
        #         underlay.padding_bottom = 0
        plot.padding_top = 0

        res = line.regressor.calculate_residuals()
        x = line.regressor.clean_xs
        # self.line = line

        xn, rn, xp, rp = self._split_residual(x, res)

        yrange = DataRange1D(ArrayDataSource(res))

        ymapper = LinearMapper(range=yrange)

        container = container_factory(
            kind="o",
            padding_left=plot.padding_left,
            padding_right=plot.padding_right,
            padding_top=50,
            padding_bottom=0,
            height=75,
            resizable="h",
        )

        neg_bar = BarPlot(
            index=ArrayDataSource(xn),
            value=ArrayDataSource(rn),
            index_mapper=scatter.index_mapper,
            value_mapper=ymapper,
            bar_width=0.2,
            line_color="blue",
            fill_color="blue",
            border_visible=True,
        )

        left_axis = PlotAxis(neg_bar, orientation="right", title="residuals")
        # bottom_axis=PlotAxis(bar,orientation='bottom')

        # kw = dict(vtitle='residuals')
        # if self.xtitle:
        #     kw['htitle'] = self.xtitle

        # add_default_axes(neg_bar, **kw)
        hgrid = PlotGrid(
            mapper=ymapper,
            component=neg_bar,
            orientation="horizontal",
            line_color="lightgray",
            line_style="dot",
        )

        neg_bar.underlays.append(hgrid)
        neg_bar.underlays.append(left_axis)

        pos_bar = BarPlot(
            index=ArrayDataSource(xp),
            value=ArrayDataSource(rp),
            index_mapper=scatter.index_mapper,
            value_mapper=ymapper,
            bar_width=0.2,
            line_color="green",
            fill_color="green",
            # bgcolor = 'green',
            resizable="hv",
            border_visible=True,
            # padding = [30, 5, 0, 30]
        )
        # bar2.overlays.append(GuideOverlay(bar2, value=0, color=(0, 0, 0)))
        # bar2.underlays.append(hgrid)
        container.add(pos_bar)
        container.add(neg_bar)
        #
        # # container.add(PlotLabel('foo'))
        #
        self.residual_plots = [neg_bar, pos_bar]
        self.plotcontainer.insert(0, container)


if __name__ == "__main__":
    import numpy as np

    g = ResidualsGraph()
    g.new_plot()

    n = 100
    x = np.arange(n)
    a, b, c = -0.01, 0, 100
    y = a * x**2 + b * x + c + 10 * np.random.random(n)
    g.new_series(x, y)

    g.configure_traits()

# ============= EOF =====================================
