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

from pychron.core.helpers.color_generators import colorname_generator
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure


class RegressionSeries(BaseArArFigure):
    def build(self, plots, plot_dict=None, *args, **kwargs):
        """
        make plots
        """

        graph = self.graph

        graph.clear_has_title()

        title = self.title
        if not title:
            title = self.options.title

        for i, po in enumerate(plots):
            kw = {"ytitle": po.name}
            if plot_dict:
                kw.update(plot_dict)

            if i == (len(plots) - 1):
                kw["title"] = title

            if i == 0 and self.ytitle:
                kw["ytitle"] = self.ytitle

            if not po.ytitle_visible:
                kw["ytitle"] = ""

            if self.xtitle:
                kw["xtitle"] = self.xtitle

            kw["padding"] = self.options.get_paddings()

            p = graph.new_plot(**kw)
            # set a tag for easy identification
            p.y_axis.tag = po.name
            self._setup_plot(i, p, po)

            # if self.options.use_legend:
            # if True:
            # self._add_legend()

    def plot(self, plots, legend=None):
        a = self.analyses[0]
        a.load_raw_data()
        cg = colorname_generator()
        graph = self.graph
        for i, po in enumerate(plots):
            name = po.name
            kind = "signal"
            if name.endswith("bs"):
                kind = "baseline"
                name = name[:-2]
            iso = a.get_isotope(name, kind=kind)
            if iso:
                xs = iso.xs
                ys = iso.ys
                self.graph.new_series(
                    xs,
                    ys,
                    fit="{}_{}".format(iso.fit, iso.error_type),
                    filter_outliers_dict=iso.filter_outliers_dict,
                    type="scatter",
                    plotid=i,
                    color=next(cg),
                    add_point_inspector=False,
                )

            if self.options.show_statistics:
                graph.add_statistics(plotid=i)


# ============= EOF =============================================
