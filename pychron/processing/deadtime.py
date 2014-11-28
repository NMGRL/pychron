# ===============================================================================
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
# ===============================================================================
from numpy import polyfit, linspace, polyval

from pychron.core.ui import set_qt


set_qt()

from itertools import groupby
from uncertainties import ufloat, nominal_value, std_dev
from pychron.core.stats import calculate_weighted_mean, calculate_mswd
from pychron.graph.graph import Graph

#============= enthought library imports =======================
from traits.api import HasTraits, Instance
from traitsui.api import View, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.csv.csv_parser import CSVColumnParser


class DeadTimeModel(HasTraits):
    def load(self, p):
        cp = CSVColumnParser()
        cp.load(p)
        self._cp = cp

    def get_raw(self):
        """
            return NShots vs 40/36
        """
        xs = []
        ys = []
        for r in self._cp.itervalues():
            xs.append(int(r['NShots']))
            ys.append(float(r['Ar40']) / float(r['Ar36']))

        return xs, ys

    def _deadtime_correct(self, v, tau):
        return v / (1 - v * tau)

    def get_mean_raw(self, tau=None):
        vs = []
        corrfunc = self._deadtime_correct
        for r in self._cp.itervalues():
            n = int(r['NShots'])
            nv = ufloat(float(r['Ar40']), float(r['Ar40err'])) * 6240
            dv = ufloat(float(r['Ar36']), float(r['Ar36err'])) * 6240
            if tau:
                dv = corrfunc(dv, tau * 1e-9)

            vs.append((n, nv / dv))

        key = lambda x: x[0]
        vs = sorted(vs, key=key)

        mxs = []
        mys = []
        mes = []
        for n, gi in groupby(vs, key=key):
            mxs.append(n)
            ys, es = zip(*[(nominal_value(xi[1]), std_dev(xi[1])) for xi in gi])

            wm, werr = calculate_weighted_mean(ys, es)
            mys.append(wm)
            mes.append(werr)

        return mxs, mys, mes

    def get_deadtime_vs_mswd(self):
        taus = range(1, 20, 1)
        ms = []
        for tau in taus:
            ns, ys, es = self.get_mean_raw(tau)
            ms.append(calculate_mswd(ys, es))
        return taus, ms

    def calculate_deadtime(self, taus, ms):
        """
            min at dy=0   (ax2+bx+c)dx=dy==2ax+b
            2ax+b=0 , x=-b/(2a)
        """

        coeffs = polyfit(taus, ms, 2)
        dt = -coeffs[1] / (2 * coeffs[0])
        fxs = linspace(min(taus), max(taus))

        return fxs, polyval(coeffs, fxs), dt


class DeadTimeGrapher(HasTraits):
    graph = Instance(Graph)

    def _graph_default(self):
        g = Graph(container_dict=dict(spacing=5))
        return g

    def _set_padding(self, p):
        p.padding = [60, 10, 10, 30]

    def rebuild(self):
        g = self.graph
        m = self.deadtime_model

        #plot raw data
        p = g.new_plot()
        self._set_padding(p)
        xs, ys = m.get_raw()
        g.new_series(xs, ys, type='scatter')
        g.set_x_title('NShots')
        g.set_y_title('40/36')

        #plot nshots vs mean
        p = g.new_plot()
        self._set_padding(p)
        xs, ys, _ = m.get_mean_raw()
        g.new_series(xs, ys, type='scatter', plotid=1)
        g.set_x_title('NShots', plotid=1)
        g.set_y_title('Mean 40/36', plotid=1)

        #plot tau vs mswd
        p = g.new_plot()
        p.value_range.tight_bounds = False
        self._set_padding(p)
        xs, ys = m.get_deadtime_vs_mswd()

        g.new_series(xs, ys, type='scatter', plotid=2)

        fxs, fys, dt = m.calculate_deadtime(xs, ys)
        g.new_series(fxs, fys, plotid=2)
        g.add_vertical_rule(dt, plotid=2)

        g.set_x_title('deadtime (ns)', plotid=2)
        g.set_y_title('MSWD', plotid=2)

    def traits_view(self):
        v = View(UItem('graph', style='custom'), resizable=True)
        return v


if __name__ == '__main__':
    p = '/Users/ross/Sandbox/deadtime_template.txt'
    d = DeadTimeModel()
    d.load(p)
    dtg = DeadTimeGrapher(deadtime_model=d)
    dtg.rebuild()
    dtg.configure_traits()



# ============= EOF =============================================

