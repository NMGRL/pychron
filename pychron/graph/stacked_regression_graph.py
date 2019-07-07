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
from traits.api import Int
from pychron.graph.regression_graph import RegressionGraph
from pychron.graph.stacked_graph import StackedGraph, ColumnStackedGraph


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


class ColumnStackedRegressionGraph(RegressionGraph, ColumnStackedGraph):
    pass


def main_regtest():
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


def main_coltest():
    from numpy import Inf, linspace
    from math import ceil
    isotopes = ['a', 'b', 'c', 'd', 'e']
    show_statistics = False
    show_evo = True
    ncols = 2
    nrows = ceil(len(isotopes)/ncols)
    g = ColumnStackedRegressionGraph(ncols=ncols, nrows=nrows, container_dict={'padding_top': 40,
                                                                               'padding_bottom': 40})
    xmi, xma = 0, -Inf

    def min_max(a, b, vs):
        return min(a, vs.min()), max(b, vs.max())

    def split(l, n):
        return [l[i:i + n] for i in range(0, len(l), n)]

    def reorder(l):
        nl = []
        for ri in range(len(l[0])):
            for col in l:
                try:
                    nl.append(col[ri])
                except IndexError:
                    pass
        return nl

    ff = split(isotopes, nrows)
    isotopes = reorder(ff)
    print('ff', ff)
    print('as', isotopes)

    for i, iso in enumerate(isotopes):
        ymi, yma = Inf, -Inf

        p = g.new_plot(padding=[80, 10, 10, 40])
        g.add_limit_tool(p, 'x')
        g.add_limit_tool(p, 'y')
        g.add_axis_tool(p, p.x_axis)
        g.add_axis_tool(p, p.y_axis)
        if show_statistics:
            g.add_statistics(i)

        p.y_axis.title_spacing = 50
        # if show_equilibration:
        #     sniff = iso.sniff
        #     if sniff.xs.shape[0]:
        #         g.new_series(sniff.offset_xs, sniff.ys,
        #                      type='scatter',
        #                      fit=None,
        #                      color='red')
        #         ymi, yma = min_max(ymi, yma, sniff.ys)
        #         xmi, xma = min_max(xmi, xma, sniff.offset_xs)

        if show_evo:
            # if iso.fit is None:
            #     iso.fit = 'linear'
            xs = linspace(0, 100)
            ys = 1000 - 0.1 * xs
            fit = 'linear'
            g.new_series(xs, ys,
                         fit=fit,
                         color='black')
            ymi, yma = min_max(ymi, yma, ys)
            xmi, xma = min_max(xmi, xma, xs)

        # if show_baseline:
        #     baseline = iso.baseline
        #     g.new_series(baseline.offset_xs, baseline.ys,
        #                  type='scatter', fit=baseline.fit,
        #                  filter_outliers_dict=baseline.filter_outliers_dict,
        #                  color='blue')
        #     ymi, yma = min_max(ymi, yma, baseline.ys)
        #     xmi, xma = min_max(xmi, xma, baseline.offset_xs)

        g.set_x_limits(min_=xmi, max_=xma, pad='0.025,0.05')
        g.set_y_limits(min_=ymi, max_=yma, pad='0.05', plotid=i)
        g.set_x_title('Time (s)', plotid=i)
        g.set_y_title(iso, plotid=i)

    g.configure_traits()


if __name__ == '__main__':
    main_coltest()
# ============= EOF =============================================
