# ===============================================================================
# Copyright 2012 Jake Ross
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
# ===============================================================================

from pychron.graph.regression_graph import RegressionGraph
from pychron.graph.stacked_graph import StackedGraph


class StackedRegressionGraph(RegressionGraph, StackedGraph):
    def new_series(self, *args, **kw):
        ret = super(StackedRegressionGraph, self).new_series(*args, **kw)
        if len(ret) == 3:
            plot, scatter, line = ret
        else:
            scatter, plot = ret

        if self.bind_index:
            bind_id = kw.get('bind_id')
            if bind_id:
                self._bind_index(scatter, bind_id)
        return ret


if __name__ == '__main__':
    rg = StackedRegressionGraph(bind_index=False)
    rg.plotcontainer.spacing = 10
    rg.new_plot()
    rg.new_plot()
    # rg.new_plot()
    from numpy.random import RandomState
    from numpy import linspace

    n = 50
    x = linspace(0, 10, n)

    rs = RandomState(123456)

    # print rs.randn(10)
    # print rs.randn(10)
    y = 5 + rs.rand(n)
    y[[1, 2, 3, 4]] = [1, 2, 3, 4]
    y2 = 10 + rs.rand(n)
    y2[[-1, -2, -3, -4]] = [6, 5, 6, 7]

    # y = 2 * x + random.rand(n)

    # d = np.zeros(n)
    # d[::10] = random.rand() + 5
    # d[::15] = random.rand() + 2

    # y += d

    fod = {'filter_outliers': False, 'iterations': 1, 'std_devs': 2}
    rg.new_series(x, y,
                  # yerror=random.rand(n)*5,
                  fit='linear_SD',
                  # truncate='x<1',
                  filter_outliers_dict=fod, plotid=0)
    rg.add_statistics(plotid=0)
    # fod = {'filter_outliers': True, 'iterations': 1, 'std_devs': 2}
    # rg.new_series(x, y,
    #               #yerror=random.rand(n)*5,
    #               fit='linear_SD',
    #               # truncate='x<1',
    #               filter_outliers_dict=fod, plotid=1)
    # fod = {'filter_outliers': True, 'iterations': 1, 'std_devs': 2}
    rg.new_series(x, y2,
                  # yerror=random.rand(n)*5,
                  fit='average_SD',
                  # truncate='x<1',
                  filter_outliers_dict=fod, plotid=1)
    rg.add_statistics(plotid=1)
    rg.set_y_limits(0, 20, plotid=0)
    rg.set_y_limits(0, 20, plotid=1)
    # rg.set_y_limits(0,20, plotid=2)
    rg.configure_traits()
# ============= EOF =============================================
