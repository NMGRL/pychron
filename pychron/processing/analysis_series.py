#===============================================================================
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
#===============================================================================
from pychron.core.ui import set_qt

set_qt()

#============= enthought library imports =======================
from traits.api import HasTraits, Instance
from traitsui.api import View, UItem
from chaco.ticks import AbstractTickGenerator

#============= standard library imports ========================
from numpy import ones_like, array
#============= local library imports  ==========================
from pychron.processing.analysis_graph import AnalysisGraph

TICKS = {1.0: 'Unknowns', 2.0: 'Airs', 3.0: 'Blanks'}


class StaticTickGenerator(AbstractTickGenerator):
    def get_ticks(self, *args, **kw):
        return array([1, 2, 3])


def tick_formatter(x):
    v = ''
    if x in TICKS:
        v = TICKS[x]
    return v


class AnalysisSeriesGraph(HasTraits):
    graph = Instance(AnalysisGraph, ())

    def build(self):
        g = self.graph
        p = g.new_plot()
        p.value_range.tight_bounds = False
        p.index_range.tight_bounds = False
        p.y_axis.tick_label_formatter = tick_formatter
        p.y_axis.tick_generator = StaticTickGenerator()
        p.y_axis.tick_label_rotate_angle = 90

        xs = [1, 2, 3, 4, 5]
        ys = ones_like(xs)
        g.new_series(xs, ys, type='scatter')

        xs = [1.1, 2.1, 3.1, 14, 15]
        ys = ones_like(xs) * 2
        g.new_series(xs, ys, type='scatter')

        xs = [10, 12, 13, 24, 25]
        ys = ones_like(xs) * 3
        g.new_series(xs, ys, type='scatter')


    def traits_view(self):
        v = View(UItem('graph',
                       # editor=InstanceEditor(),
                       style='custom'))
        return v


if __name__ == '__main__':
    a = AnalysisSeriesGraph()
    a.build()
    a.configure_traits()

#============= EOF =============================================

