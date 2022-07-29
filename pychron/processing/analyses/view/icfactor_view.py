# ===============================================================================
# Copyright 2022 ross
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
from chaco.array_data_source import ArrayDataSource
from chaco.plot_containers import HPlotContainer
from traits.api import HasTraits, Instance, Any
from traitsui.api import View, UItem
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.dvc import ICFACTORS
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.stacked_graph import StackedGraph


class ICFactorView(HasTraits):
    name = "ICFactor"
    # container = Instance(HPlotContainer)
    analysis = Any
    dvc = Any
    graph = Instance(StackedGraph)

    # def initialize(self, an):
    #     # an.load_raw_data()
    #     self.analysis = an
    #     self.setup_graph(an)

    def activate(self):
        if not self.graph:
            self.setup_graph()

    def setup_graph(self):
        container_dict = {"spacing": 5, "stack_order": "top_to_bottom"}
        sg = StackedGraph(container_dict=container_dict)

        obj, _ = self.analysis.get_json(ICFACTORS)
        if obj:
            keys = obj.keys()
            for k in sort_isotopes(keys):
                iso = obj[k]
                rd = iso.get('reference_data')
                if rd:
                    pp = sg.new_plot(ytitle='Reference Ratio', xtitle='Time (hrs)')

                    pp.padding_left = 100
                    pp.padding_bottom = 100
                    xs = rd['xs']

                    cx = (self.analysis.timestamp - xs[-1]) / 3600.
                    xs = [(xi-xs[-1])/3600. for xi in xs]

                    ys = rd['vs']
                    es = rd['es']
                    mi = min([yi-ei for yi,ei in zip(ys,es)])
                    ma = max([yi+ei for yi,ei in zip(ys,es)])

                    scatter, _ = sg.new_series(xs, ys, type='scatter')

                    ebo = ErrorBarOverlay(
                        component=scatter,
                        orientation='y',
                        # nsigma=1,
                        # visible=visible,
                        # line_width=line_width,
                        # use_end_caps=end_caps,
                    )

                    scatter.underlays.append(ebo)
                    scatter.yerror = ArrayDataSource(es)
                    sg.add_horizontal_rule(1)

                    iso = self.analysis.get_isotope(detector=k)

                    scatter, _ = sg.new_series([cx], [nominal_value(iso.ic_factor)], type='scatter')
                    ebo = ErrorBarOverlay(
                        component=scatter,
                        orientation='y',
                    )

                    scatter.underlays.append(ebo)
                    scatter.yerror = ArrayDataSource([std_dev(iso.ic_factor)])

                    sg.set_y_limits(min_=min(1, mi), max_=ma, pad='0.1')
                    sg.set_x_limits(pad='0.1')

        self.graph = sg

    def traits_view(self):
        return View(UItem('graph', style='custom'))
# ============= EOF =============================================
