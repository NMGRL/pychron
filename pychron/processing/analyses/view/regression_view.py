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
from traits.api import HasTraits, Instance
from traitsui.api import View, UItem

from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.stacked_regression_graph import StackedRegressionGraph


class RegressionView(HasTraits):
    name = 'Regressions'
    container = Instance(HPlotContainer)

    def initialize(self, an):
        an.load_raw_data()
        self.setup_graph(an)

    def setup_graph(self, an):

        container = HPlotContainer()

        sg = StackedGraph()
        sg.plotcontainer.spacing = 5
        sg.plotcontainer.stack_order = 'top_to_bottom'

        isos = an.sorted_values(reverse=False)
        for iso in isos:
            sniff = iso.sniff
            sg.new_plot(ytitle=iso.name, xtitle='Time (s)', title='Equilibration')
            if sniff.xs.shape[0]:
                sg.new_series(sniff.xs, sniff.ys, marker='circle', type='scatter')

        bg = StackedRegressionGraph()
        bg.plotcontainer.spacing = 5
        bg.plotcontainer.stack_order = 'top_to_bottom'

        for iso in isos:
            baseline = iso.baseline
            bg.new_plot(ytitle=baseline.detector, xtitle='Time (s)', title='Baseline')
            if baseline.xs.shape[0]:
                bg.new_series(baseline.xs, baseline.ys,
                              color='red', type='scatter', fit=baseline.fit)

        ig = StackedRegressionGraph()
        ig.plotcontainer.spacing = 5
        ig.plotcontainer.stack_order = 'top_to_bottom'

        for iso in isos:
            ig.new_plot(ytitle=iso.name, xtitle='Time (s)', title='Isotope')
            if iso.xs.shape[0]:
                ig.new_series(iso.xs, iso.ys,
                              color='blue', type='scatter', fit=iso.fit)

        container.add(sg.plotcontainer)
        container.add(ig.plotcontainer)
        container.add(bg.plotcontainer)

        self.container = container

    def traits_view(self):
        v = View(UItem('container', style='custom', editor=ComponentEditor()),
                 resizable=True)
        return v


if __name__ == '__main__':
    r = RegressionView()
    r.setup_graph(None)
    r.configure_traits()


# ============= EOF =============================================
