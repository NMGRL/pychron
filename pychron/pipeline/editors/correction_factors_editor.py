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
from __future__ import absolute_import
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.stats import calculate_weighted_mean, calculate_mswd
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from traits.api import HasTraits, Int, Str, Float, List, Instance
from traitsui.api import View, UItem, Item, HGroup, VGroup, TabularEditor
from numpy import array

from pychron.graph.graph import Graph
from pychron.graph.stacked_graph import StackedGraph
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA
from six.moves import range


class Result(HasTraits):
    value = Float
    error = Float
    name = Str
    wm_value = Float
    wm_error = Float
    mswd = Float

    def __init__(self, ratios, name, *args, **kw):
        super(Result, self).__init__(*args, **kw)
        vs = array([nominal_value(ri) for ri in ratios])
        es = array([std_dev(ri) for ri in ratios])

        self.name = name
        m = ratios.mean()
        self.value = nominal_value(m)
        self.error = std_dev(m)
        wm, we = calculate_weighted_mean(vs, es)
        self.wm_value = wm
        self.wm_error = we
        self.mswd = calculate_mswd(vs, es, wm=wm)


class ResultsAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Mean', 'value'),
               (PLUSMINUS_ONE_SIGMA, 'error'),
               ('Wt. Mean', 'wm_value'),
               (PLUSMINUS_ONE_SIGMA, 'wm_error'),
               ('MSWD', 'mswd')
               ]


class CorrectionFactorsEditor(BaseTraitsEditor):
    analyses = List
    results = List
    graph = Instance(StackedGraph, ())

    def initialize(self):
        self.calculate()

    def calculate(self):
        # nx = array([a.corrected_intensities[nkey] for a in self.analyses])
        # ny = array([a.corrected_intensities[dkey] for a in self.analyses])

        for a in self.analyses:
            a.calculate_no_interference()

        for n, d, tag in (('rad40', 'k39', '(40/39)K'),
                          ('ca36', 'ca39', '(36/39)Ca'),
                          ('ca37', 'ca39', '(37/39)Ca')):
            try:
                rs = [a.computed[n] / a.computed[d] for a in self.analyses]

                self.results.append(Result(array(rs), tag))
                plot = self.graph.new_plot()
                plot.x_axis.title = tag
                self.graph.new_series([nominal_value(ri) for ri in rs], list(range(len(rs))), type='scatter')
                plot = self.graph.new_plot()
            except ZeroDivisionError:
                pass

    def traits_view(self):
        v = View(VGroup(UItem('results', editor=TabularEditor(adapter=ResultsAdapter())),
                        UItem('graph', style='custom')))
        return v

# ============= EOF =============================================
