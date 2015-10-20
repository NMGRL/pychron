# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Instance, Float
from traitsui.api import View, Item, UItem, VGroup
# ============= standard library imports ========================
from uncertainties import nominal_value
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.stacked_regression_graph import StackedRegressionGraph


class RatioEditor(BaseTraitsEditor):
    """
    """
    graph = Instance(StackedRegressionGraph)

    intercept_ratio = Float
    time_zero_offset = Float(0, auto_set=False, enter_set=True)
    ratio_intercept = Float

    basename = ''
    def _time_zero_offset_changed(self):
        self.refresh_plot()

    def setup(self):
        self.data = self.analysis.isotopes
        self.setup_graph()

    def setup_graph(self):
        cd = dict(padding=20,
                  spacing=5,
                  stack_order='top_to_bottom')
        g = StackedRegressionGraph(container_dict=cd)
        self.graph = g
        self.refresh_plot()

    def refresh_plot(self):
        g = self.graph
        d = self.data

        g.clear()

        for ni, di in [('Ar40', 'Ar39')]:
            niso, diso = d[ni], d[di]
            self.plot_ratio(g, niso, diso)

            self.intercept_ratio = nominal_value(niso.uvalue / diso.uvalue)

    def plot_ratio(self, g, niso, diso):
        niso.time_zero_offset = self.time_zero_offset
        diso.time_zero_offset = self.time_zero_offset

        fd = {'filter_outliers': True, 'std_devs': 2, 'iterations': 1}

        niso.filter_outliers_dict = fd
        diso.filter_outliers_dict = fd
        niso.dirty = True
        diso.dirty = True

        g.new_plot()
        g.set_x_limits(min_=0, max_=100)
        g.set_y_title(niso.name)
        _,_,nl = g.new_series(niso.offset_xs, niso.ys, filter_outliers_dict=fd)

        g.new_plot()
        g.set_y_title(diso.name)
        _,_,dl = g.new_series(diso.offset_xs, diso.ys, filter_outliers_dict=fd)

        # g.new_plot()
        # nreg = nl.regressor
        # dreg = dl.regressor
        #
        # xs = nreg.xs
        # ys = nreg.predict(xs)/dreg.predict(xs)
        # _,_,l =g.new_series(xs, ys, fit='parabolic')
        # reg = l.regressor
        # self.regressed_ratio_intercept = reg.predict(0)

        # xs = linspace(0, 100)
        # rys = niso.regressor.predict(xs) / diso.regressor.predict(xs)
        xs = niso.offset_xs
        rys = niso.ys / diso.ys

        g.new_plot()
        g.set_y_title('{}/{}'.format(niso.name, diso.name))
        g.set_x_title('Time (s)')
        # p,s,l = g.new_series(xs, rys, fit='parabolic', filter_outliers_dict=fd)

        fd = {'filter_outliers': True, 'std_devs': 2, 'iterations': 1}

        fitfunc = lambda p, x: (p[0]*x+p[1])/(p[2]*x+p[3])

        fit = ((fitfunc, [1,1,1,1]), None)
        p,s,l = g.new_series(xs, rys, fit=fit,
                             use_error_envelope=False,
                             filter_outliers_dict=fd)
        reg = l.regressor
        self.ratio_intercept = reg.predict(0)


    def traits_view(self):
        v = View(UItem('graph', style='custom'),
                 VGroup(Item('time_zero_offset'),
                        Item('intercept_ratio', style='readonly'),
                        Item('ratio_intercept', style='readonly')))
        return v


if __name__ == '__main__':
    re = RatioEditor()
    re.setup()
    re.configure_traits()
# ============= EOF =============================================



