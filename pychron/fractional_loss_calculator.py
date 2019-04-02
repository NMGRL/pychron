# ===============================================================================
# Copyright 2019 ross
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
from numpy import linspace
from traits.api import HasTraits, Int, Float, Instance, on_trait_change
from traitsui.api import View, VGroup, UItem, Item, HGroup

from pychron.graph.graph import Graph
from pychron.processing.argon_calculations import calculate_fractional_loss


class FractionalLossCalculator(HasTraits):
    graph = Instance(Graph)
    temp = Float(475)
    min_age = Int(1)
    max_age = Int(1000)
    radius = Float(0.1)

    def __init__(self, *args, **kw):
        super(FractionalLossCalculator, self).__init__(*args, **kw)

        self.graph = g = Graph()
        g.new_plot()

        xs, ys = self._calculate_data()
        g.new_series(xs, ys)

    def _calculate_data(self):
        xs = linspace(self.min_age, self.max_age)
        fs = [calculate_fractional_loss(ti, self.temp, self.radius) for ti in xs]
        return xs, fs

    @on_trait_change('temp, radius, max_age, min_age')
    def _replot(self):
        xs, ys = self._calculate_data()

        self.graph.set_data(xs)
        self.graph.set_data(ys, axis=1)

    def traits_view(self):
        a = HGroup(Item('temp'), Item('radius'), Item('min_age'), Item('max_age'))
        v = View(VGroup(a, UItem('graph', style='custom')))
        return v


if __name__ == '__main__':
    f = FractionalLossCalculator()
    f.configure_traits()
# ============= EOF =============================================
