from pychron.graph.regression_graph import RegressionGraph
from pychron.graph.stacked_graph import StackedGraph

__author__ = 'ross'


class StackedRegressionGraph(RegressionGraph, StackedGraph):
    pass


if __name__ == '__main__':
    rg = StackedRegressionGraph(bind_index=False)
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
                  #yerror=random.rand(n)*5,
                  fit='linear_SD',
                  # truncate='x<1',
                  filter_outliers_dict=fod)
    # fod = {'filter_outliers': True, 'iterations': 1, 'std_devs': 2}
    # rg.new_series(x, y,
    #               #yerror=random.rand(n)*5,
    #               fit='linear_SD',
    #               # truncate='x<1',
    #               filter_outliers_dict=fod, plotid=1)
    # fod = {'filter_outliers': True, 'iterations': 1, 'std_devs': 2}
    rg.new_series(x, y2,
                  #yerror=random.rand(n)*5,
                  fit='average_SD',
                  # truncate='x<1',
                  filter_outliers_dict=fod, plotid=1)
    rg.set_y_limits(0, 20, plotid=0)
    rg.set_y_limits(0, 20, plotid=1)
    # rg.set_y_limits(0,20, plotid=2)
    rg.configure_traits()