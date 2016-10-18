# ===============================================================================
# Copyright 2016 ross
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
import os

import yaml
from numpy import array
from traits.api import Float, Button, Property, List, Instance, Bool, Event
from traitsui.api import View, UItem, Item, HGroup, VGroup
from uncertainties import nominal_value, std_dev

from pychron.core.stats.core import calculate_weighted_mean
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.paths import paths
from pychron.processing.analysis_graph import AnalysisStackedRegressionGraph


class YieldEditor(BaseTraitsEditor):
    analyses = List

    current_yield = Float(1.0)
    new_yield = Property(depends_on='current,current_yield,standard_ratio,refresh_current,references')
    current = Property(Float, depends_on='use_weighted_mean, refresh_current')
    standard_ratio = Float
    _current = Float

    refresh_current = Event
    use_weighted_mean = Bool(True)

    set_yield_button = Button('Set Yield')
    revert_button = Button('Revert')

    graph = Instance(AnalysisStackedRegressionGraph)
    options = None

    def initialize(self):
        self.load()
        self.replot()

    def set_items(self, items):
        self.analyses = items
        self.replot()

    def replot(self):
        graph = self.graph
        if graph is None:
            graph = AnalysisStackedRegressionGraph()
        else:
            graph.clear()

        vs = self._get_values(scalar=self.standard_ratio)
        xs = self._get_xs()

        graph.new_plot()

        plot, scatter, line = graph.new_series(x=xs, y=vs[0],
                                               fit='weighted mean',
                                               yerror=vs[1], type='scatter')

        ebo = ErrorBarOverlay(component=scatter,
                              orientation='y')
        scatter.overlays.append(ebo)

        graph.set_x_title('Time (hrs)')
        graph.set_y_title(self.options.ratio_str)

        graph.set_y_limits(min_=min([v - e for v, e in zip(*vs)]),
                           max_=max([v + e for v, e in zip(*vs)]), pad='0.1')
        graph.set_x_limits(min_=min(xs), max_=max(xs), pad='0.1')

        graph.refresh()
        self.graph = graph

    def _calculate_current(self, vs=None):
        if vs is None:
            vs = self._get_values()

        xs, es = vs
        if self.use_weighted_mean:
            return calculate_weighted_mean(xs, es)
        else:
            xs = array(xs)
            return xs.mean(), xs.std()

    def _get_xs(self):
        vs = sorted((ai.timestamp for ai in self.analyses))
        vo = vs[0]
        return [(vi - vo) / 3600. for vi in vs]

    def _get_values(self, scalar=None):
        r = self.options.ratio_str
        vs = [getattr(ai, r) for ai in self.analyses]
        if scalar:
            vs = [vi/scalar for vi in vs]
        ys = map(nominal_value, vs)
        es = map(std_dev, vs)

        return ys, es

    def _get_current(self):
        if self._current:
            m = self._current
        else:
            m, e = self._calculate_current()
        return m

    def _set_current(self, v):
        self._current = v
        self.refresh_current = True

    def _get_new_yield(self):
        """
        yield  == 1/gain

        increase yield increase 40/36 ratio
        @return:
        """

        return self.standard_ratio / self.current * self.current_yield

    def dump(self):
        with open(self.yield_path, 'w') as wfile:
            yaml.dump({'{}_yield'.format(self.options.ratio_str): self.new_yield}, wfile)

    def load(self):
        p = self.yield_path
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                yd = yaml.load(rfile)
                key = '{}_yield'.format(self.options.ratio_str)
                try:
                    self.current_yield = yd[key]
                except KeyError:
                    pass

    @property
    def yield_path(self):
        p = os.path.join(paths.hidden_dir, 'yield.yaml')
        return p

    # handlers
    def _revert_button_fired(self):
        self._current = 0
        self.refresh_current = True

    def _set_yield_button_fired(self):
        self.dump()

    def traits_view(self):
        ctrl_grp = VGroup(Item('use_weighted_mean'),
                          HGroup(Item('standard_ratio'),Item('current_yield')),
                          HGroup(Item('current'), UItem('revert_button')),
                          HGroup(Item('new_yield'), UItem('set_yield_button')))

        graph_grp = VGroup(UItem('graph', style='custom'))
        v = View(VGroup(ctrl_grp, graph_grp))
        return v

# ============= EOF =============================================
