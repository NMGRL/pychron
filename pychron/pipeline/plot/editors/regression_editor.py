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
from traits.api import Instance, Str
from chaco.array_data_source import ArrayDataSource

from numpy import linspace, ones_like

from pychron.core.regression.new_york_regressor import NewYorkRegressor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor

from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.graph import Graph
from pychron.graph.regression_graph import RegressionGraph


class RegressionEditor(BaseTraitsEditor):
    graph = Instance(Graph)
    result_str = Str
    result_template = '''
mswd={mswd:}
slope={slope:}
intercept={intercept:}
rsquared={rsquared:}
'''

    def set_items(self, items):
        print(items)
        xs = [r.x for r in items]
        xe = [r.x_err for r in items]
        ys = [r.y for r in items]
        ye = [r.y_err for r in items]
        print(self.plotter_options)

        g = Graph()
        g.new_plot()
        scatter, plot = g.new_series(xs, ys, type='scatter')

        kw = {}
        if any(xe):
            kw['xserr'] = xe
            # kw['xnes'] = xe
            ebo = ErrorBarOverlay(component=scatter,
                                  orientation='x',
                                  # nsigma=nsigma,
                                  # visible=visible,
                                  # line_width=line_width,
                                  # use_end_caps=end_caps
                                  )
            scatter.underlays.append(ebo)
            setattr(scatter, 'xerror', ArrayDataSource(xe))

        if any(ye):
            kw['yserr'] = ye
            # kw['ynes'] = ye
            ebo = ErrorBarOverlay(component=scatter,
                                  orientation='y',
                                  # nsigma=nsigma,
                                  # visible=visible,
                                  # line_width=line_width,
                                  # use_end_caps=end_caps
                                  )
            scatter.underlays.append(ebo)
            setattr(scatter, 'yerror', ArrayDataSource(ye))

        reg_klass = NewYorkRegressor
        reg = reg_klass(xns=xs, yns=ys,
                        xs=xs, ys=ys,
                        # xds=ones_like(xs),
                        # yds=ones_like(xs),
                        # xdes=ones_like(xs),
                        # ydes=ones_like(xs),
                        degree=1,
                        **kw)
        reg.calculate()

        pad = (max(xs)-min(xs))*0.1
        l = min(xs)-pad
        u = max(xs)+pad
        fx = linspace(l, u)
        m, b = reg.get_slope(), reg.get_intercept()
        fy = fx * m + b
        g.new_series(fx, fy)

        # g = RegressionGraph()
        # g.new_plot()
        # g.new_series()

        self.result_str = self.result_template.format(mswd=reg.mswd, slope=reg.slope,
                                                      intercept=reg.intercept,
                                                      rsquared=reg.rsquared)
        self.graph = g

    def traits_view(self):
        return View(UItem('graph', style='custom'),
                    UItem('result_str', style='custom', editor=TextEditor(read_only=True)))

# ============= EOF =============================================
