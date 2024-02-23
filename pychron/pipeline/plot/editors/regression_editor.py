# ===============================================================================
# Copyright 2021 ross
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
from traitsui.api import View, UItem, TextEditor
from traits.api import Instance, Str, Event, List
from chaco.array_data_source import ArrayDataSource

from numpy import linspace, ones_like, array

from pychron.core.helpers.formatting import floatfmt
from pychron.core.regression.new_york_regressor import NewYorkRegressor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor

from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.graph import Graph
from pychron.graph.regression_graph import RegressionGraph
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.options.regression import RegressionOptions
from pychron.processing.analysis_graph import AnalysisGraph


class SimpleRegressionGraph(Graph):
    pass


class RegressionEditor(BaseTraitsEditor):
    graph = Instance(Graph)
    plotter_options = Instance(RegressionOptions)
    result_str = Str
    result_template = """
mswd={mswd:}
slope={slope:}
intercept={intercept:}
rsquared={rsquared:}
"""
    refresh_needed = Event
    _items = List

    def set_items(self, items):
        self._items = items
        self.refresh_needed = True

    def _refresh_needed_fired(self):
        items = self._items
        xs = array([r.x for r in items])
        xe = array([r.x_err for r in items])
        ys = array([r.y for r in items])
        ye = array([r.y_err for r in items])

        opt = self.plotter_options
        g = SimpleRegressionGraph(container_dict={"bgcolor": opt.bgcolor})

        kw = {}
        xerror_bar = False
        if any(xe):
            kw["xserr"] = xe
            xerror_bar = True

        yerror_bar = False
        if any(ye):
            kw["yserr"] = ye
            yerror_bar = True

        g.new_plot(ytitle=opt.ytitle, xtitle=opt.xtitle, padding=opt.get_paddings())

        reg_klass = NewYorkRegressor
        reg = reg_klass(
            xns=xs,
            yns=ys,
            xs=xs,
            ys=ys,
            # xds=ones_like(xs),
            # yds=ones_like(xs),
            # xdes=ones_like(xs),
            # ydes=ones_like(xs),
            degree=1,
            **kw
        )
        reg.calculate()

        pad = (max(xs + xe) - min(xs - xe)) * 0.1
        l = min(xs - xe) - pad
        u = max(xs + xe) + pad
        fx = linspace(l, u)
        m, b = reg.get_slope(), reg.get_intercept()
        fy = fx * m + b

        scatter, plot = g.new_series(xs, ys, type="scatter")

        g.new_series(
            fx, fy, color=opt.regression_color, line_width=opt.regression_width
        )

        plot.bgcolor = opt.plot_bgcolor
        plot.x_grid.visible = opt.use_xgrid
        plot.y_grid.visible = opt.use_ygrid

        g.add_axis_tool(plot, plot.x_axis)
        g.add_axis_tool(plot, plot.y_axis)

        inspector = AnalysisPointInspector(
            scatter,
            use_pane=False,
            analyses=items,
            include_x=True,
            # convert_index=convert_index,
            # index_tag=index_tag,
            # index_attr=index_attr,
            # value_format=value_format,
            # additional_info=additional_info
        )

        pinspector_overlay = PointInspectorOverlay(component=scatter, tool=inspector)
        scatter.overlays.append(pinspector_overlay)
        # broadcaster.tools.append(inspector)
        scatter.tools.append(inspector)

        if xerror_bar:
            ebo = ErrorBarOverlay(
                component=scatter,
                orientation="x",
                # nsigma=nsigma,
                # visible=visible,
                # line_width=line_width,
                # use_end_caps=end_caps
            )
            scatter.underlays.append(ebo)
            setattr(scatter, "xerror", ArrayDataSource(xe))

        if yerror_bar:
            ebo = ErrorBarOverlay(
                component=scatter,
                orientation="y",
                # nsigma=nsigma,
                # visible=visible,
                # line_width=line_width,
                # use_end_caps=end_caps
            )
            scatter.underlays.append(ebo)
            setattr(scatter, "yerror", ArrayDataSource(ye))

        self.result_str = self.result_template.format(
            mswd=reg.mswd,
            slope=reg.slope,
            intercept=reg.intercept,
            rsquared=reg.rsquared,
        )
        self.graph = g

    def traits_view(self):
        return View(
            UItem("graph", style="custom"),
            UItem("result_str", style="custom", editor=TextEditor(read_only=True)),
        )


# ============= EOF =============================================
