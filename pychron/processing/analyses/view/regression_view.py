# ===============================================================================
# Copyright 2018 ross
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
from chaco.plot_containers import HPlotContainer
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Instance, Any
from traitsui.api import View, UItem

from pychron.core.helpers.formatting import format_percent_error, errorfmt
from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.graph.tools.regression_inspector import RegressionInspectorTool
from pychron.pychron_constants import PLUSMINUS


class AnalysisRegressionInspectorTool(RegressionInspectorTool):
    analysis = Any

    def assemble_lines(self):
        lines = super(AnalysisRegressionInspectorTool, self).assemble_lines()
        an = self.analysis
        a = an.age

        ef = errorfmt(a, an.age_err)
        ef_wo_j = errorfmt(a, an.age_err_wo_j)
        lines.insert(0, 'Date={:0.4f} {}{} w/o_J={}'.format(a, PLUSMINUS, ef, ef_wo_j))
        return lines


class AnalysisRegressionGraph(StackedRegressionGraph):
    analysis = Any

    def regression_inspector_factory(self, line):
        tool = AnalysisRegressionInspectorTool(component=line, analysis=self.analysis)
        return tool


class RegressionView(HasTraits):
    name = 'Regressions'
    container = Instance(HPlotContainer)
    analysis = Any

    def initialize(self, an):
        an.load_raw_data()
        self.analysis = an
        self.setup_graph(an)

    def setup_graph(self, an):

        container = HPlotContainer()

        container_dict = {'spacing': 5, 'stack_order': 'top_to_bottom'}
        sg = StackedGraph(container_dict=container_dict)
        bg = AnalysisRegressionGraph(container_dict=container_dict, analysis=an)
        ig = AnalysisRegressionGraph(container_dict=container_dict, analysis=an)

        isos = an.sorted_values(reverse=False)

        sisos = [iso for iso in isos if iso.sniff.offset_xs.shape[0]]
        for i, iso in enumerate(sisos):
            sniff = iso.sniff
            p = sg.new_plot(ytitle=iso.name, xtitle='Time (s)', title='Equilibration')
            sg.add_axis_tool(p, p.x_axis)
            sg.add_axis_tool(p, p.y_axis)

            sg.new_series(sniff.offset_xs, sniff.ys, marker='circle', type='scatter')
            sg.set_y_limits(pad='0.1', plotid=i)
            sg.set_x_limits(min_=0, max_=max(sniff.offset_xs) * 1.05, plotid=i)

        iisos = [iso for iso in isos if iso.offset_xs.shape[0]]
        baselines = []
        for i, iso in enumerate(iisos):
            if iso.baseline.offset_xs.shape[0]:
                baselines.append(iso.baseline)

            p = ig.new_plot(ytitle='{}({})'.format(iso.name, iso.detector), xtitle='Time (s)', title='Isotope')
            ig.add_axis_tool(p, p.x_axis)
            ig.add_axis_tool(p, p.y_axis)

            ig.new_series(iso.offset_xs, iso.ys,
                          display_filter_bounds=True,
                          filter_outliers_dict=iso.filter_outliers_dict,
                          color='blue', type='scatter', fit=iso.efit)
            ig.set_regressor(iso.regressor, i)
            ig.set_y_limits(pad='0.1', plotid=i)
            ig.set_x_limits(min_=0, max_=max(iso.offset_xs) * 1.05, plotid=i)

        ig.refresh()
        ig.on_trait_change(self.handle_regression, 'regression_results')

        for i, baseline in enumerate(baselines):
            p = bg.new_plot(ytitle=baseline.detector, xtitle='Time (s)', title='Baseline')
            bg.add_axis_tool(p, p.x_axis)
            bg.add_axis_tool(p, p.y_axis)
            bg.new_series(baseline.offset_xs, baseline.ys,
                          filter_outliers_dict=baseline.filter_outliers_dict,
                          display_filter_bounds=True,
                          color='red', type='scatter', fit=baseline.efit)
            bg.set_regressor(baseline.regressor, i)
            bg.set_y_limits(pad='0.1', plotid=i)
            bg.set_x_limits(pad='0.025', plotid=i)

        bg.refresh()

        container.add(sg.plotcontainer)
        container.add(ig.plotcontainer)
        container.add(bg.plotcontainer)

        self.container = container

    def handle_regression(self, new):
        if new:
            for plot, regressor in new:
                for k, iso in self.analysis.isotopes.items():
                    yt = plot.y_axis.title
                    if k == yt or '{}({})'.format(iso.name, iso.detector) == yt:
                        iso.set_fit(regressor.get_fit_dict())
                        break

            self.analysis.calculate_age(force=True)
            self.analysis.analysis_view.refresh()

    def traits_view(self):
        v = View(UItem('container', style='custom', editor=ComponentEditor()),
                 resizable=True)
        return v

# ============= EOF =============================================
