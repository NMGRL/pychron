#===============================================================================
# Copyright 2011 Jake Ross
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



from traits.api import HasTraits, Instance, Button
from traitsui.api import View, Item

from numpy import array, polyfit, polyval, ones, zeros, hstack, sum
from numpy.ma import masked_array
import csv
from pychron.graph.graph import Graph
from pychron.data_processing.regression.regressor import Regressor
from threading import Thread
from pychron.graph.stacked_graph import StackedGraph

from multiprocessing import Pool
from pychron.data_processing.regression.ols import OLS
from pychron.stats import calculate_mswd


def mcalculate_mswd(d):
    return calculate_mswd(*d)


def regress(d, degree=2):

#    coeffs = polyfit(x, y, degree)
#    o = OLS(x, y, fitdegree=degree)
    o = OLS(*d, fitdegree=degree)
    return [o.get_coefficients()[2], o.get_coefficient_standard_errors()[2]]


class CountAnalyzer(HasTraits):
    graph = Instance(Graph)
    regressor = Instance(Regressor)
    test = Button

    def _regressor_default(self):
        r = Regressor()
        return r

    def _graph_default(self):
        g = StackedGraph()
        g.new_plot(show_legend=True, padding=[30, 20, 10, 40], ytitle='Ar40', xtitle='# points')
        g.new_plot(padding=[30, 20, 10, 10], ytitle='Ar40_err')
        g.new_plot(padding=[30, 20, 10, 40], ytitle='Ar36')
        g.new_plot(padding=[30, 20, 10, 10], ytitle='Ar36_err')
        g.new_plot(padding=[30, 20, 10, 10], ytitle='Ar40/Ar36')
        g.new_plot(padding=[30, 20, 10, 10], ytitle='%Diff')
        #        g.new_plot(padding=[20, 20, 10, 10], ytitle='Ar40_err')
        return g

    def traits_view(self):
        v = View(Item('test', show_label=False),
                 Item('graph', show_label=False, style='custom'), resizable=True,
                 height=0.92,
                 width=0.55
        )
        return v

    def calculate_intercept(self, xs, ys):
        args = self.regressor.parabolic(xs, ys)
        return args['coefficients'][2], args['coeff_errors'][2]

    def read_signal_data(self, reader, xs, ys):
        _name, n = reader.next()
        n = int(n)
        for _ in range(n):
            x, y = map(float, reader.next())
            xs.append(x)
            ys.append(y)

    def load_data2(self):
        oxs_40 = []
        oys_40 = []
        oxs_39 = []
        oys_39 = []
        oxs_38 = []
        oys_38 = []
        oxs_37 = []
        oys_37 = []
        oxs_36 = []
        oys_36 = []
        p = '/Users/ross/Desktop/counting exp/peak-time1200s'
        with open(p, 'U') as f:
            reader = csv.reader(f, delimiter='\t')
            # first line is runid
            _rid = reader.next()[0]

            # second line is signal name and num points

            self.read_signal_data(reader, oxs_40, oys_40)
            self.read_signal_data(reader, oxs_39, oys_39)
            self.read_signal_data(reader, oxs_38, oys_38)
            self.read_signal_data(reader, oxs_37, oys_37)
            self.read_signal_data(reader, oxs_36, oys_36)

        return oxs_40, oys_40, oxs_39, oys_39, oxs_38, oys_38, oxs_37, oys_37, oxs_36, oys_36

    def load_data(self, rid, **kw):
        p = '/Users/ross/Desktop/counting exp/peak-time1500s-40-{}'.format(rid)
        xs1, ys1, omits1 = self._load_isotope_peak_time_data(p, **kw)

        p = '/Users/ross/Desktop/counting exp/peak-time1500s-36-{}'.format(rid)
        xs2, ys2, omits2 = self._load_isotope_peak_time_data(p, **kw)
        self.omits = omits1
        return xs1, ys1, xs2, ys2

    def _load_isotope_peak_time_data(self, p, do_omit=False):
        xs = []
        ys = []
        omits = []
        with open(p, 'U') as f:
            reader = csv.reader(f, delimiter='\t')
            for _ in range(7):
                reader.next()
            while 1:
                l = reader.next()
                if len(l) == 0:
                    break

                if do_omit:
                    omit = False if l[1] == 'OK' else True
                else:
                    omit = False

                if not omit:
                    xs.append(float(l[2]))
                    ys.append(float(l[4]))
                    omits.append(l[1])

        return xs, ys, omits

    def _detect_outliers_by_cluster(self, xs, ys, outs, degree=2):
        xs = array(xs)
        ys = array(ys)

        m = ys.mean()
        sd = ys.std()

        for i, yi in enumerate(ys):
            print m, yi, sd, abs(yi - m) > (sd * 2)
            outs[i] = 1 if abs(yi - m) > (sd * 2) else 0

        return outs

    def _detect_outliers(self, xs, ys, outs, degree=2):
        xs = array(xs)
        ys = array(ys)

        mxs = masked_array(xs, mask=outs)
        #        print 's', sum(mxs), outs
        mys = masked_array(ys, mask=outs)
        o = OLS(mxs, mys, fitdegree=degree)
        coeffs = o.get_coefficients()

        n = len(xs) - sum(outs)
        #        coeff_errs = o.get_coefficient_standard_errors()

        #        ymean = ys.mean()
        yeval = polyval(coeffs, xs)

        # calculate detection_tol. use error of fit
        devs = abs(ys - yeval)
        ssr = sum(devs ** 2)
        detection_tol = 2.5 * (ssr / ((n) - (degree))) ** 0.5

        for i, xi, ys, di, mi in zip(xrange(len(xs)), xs, ys, devs, outs):
            if di > detection_tol:
                outs[i] = 1
            omit = 'OK' if di <= detection_tol and not mi else 'User omitted'
            # print xi, ys, di, detection_tol, omit, mi
        return outs

    def analyze_count_times(self, rids=None, do_omits=None, colors=None):
        if rids is None:
            rids = ['']
        if do_omits is None:
            do_omits = [True] * len(rids)
        if colors is None:
            colors = [None] * len(rids)
            # load the file
        #        args = self.load_data2()
        for rid, do_omit, color in zip(rids, do_omits, colors):
            args = self.load_data(rid, do_omit=do_omit)
            oxs_40, oys_40 = args[0], args[1]
            oxs_36, oys_36 = args[-2], args[-1]

            nsteps = 4
            pool = Pool(processes=10)

            xs = range(50, len(oxs_40), nsteps)
            result40 = pool.map(regress, [(oxs_40[:i], oys_40[:i]) for i in xs])
            result36 = pool.map(regress, [(oxs_36[:i], oys_36[:i]) for i in xs])

            kw = dict(color=color) if color else dict()

            io40, io40_e = array(result40).transpose()
            self.graph.new_series(xs, io40, plotid=0, **kw)
            self.graph.new_series(xs, io40_e, plotid=1, **kw)

            io36, io36_e = array(result36).transpose()
            self.graph.new_series(xs, io36, plotid=2, **kw)
            self.graph.new_series(xs, io36_e, plotid=3, **kw)

            r = io40 / io36
            self.graph.new_series(xs, r, plotid=4, **kw)

            ro = r[-1]
            ys = (r - ro) / ro * 100
            #        mswd calculation
            #        err = ((io40_e / io40) ** 2 + (io36_e / io36) ** 2) ** 0.5 * r
            # #        for ri, ei in zip(r, err):
            # #            print ri, ei
            #        resultmswd = pool.map(mcalculate_mswd, [(r[:i], err[:i]) for i in range(len(r))])
            self.graph.new_series(xs, ys, plotid=5, **kw)

        self.graph.redraw()

    def _test_fired(self):
        t = Thread(target=self.analyze_count_times, kwargs=dict(rids=['769', '769'],
                                                                # colors=['black', 'green'],
                                                                do_omits=[False, True]
        ))
        t.start()

    #        time.sleep(2)
#        t = Thread(target=self.analyze_count_times, kwargs=dict(rid='769', color='green', do_omit=True))
#        t.start()
#
#        t = Thread(target=self.analyze_count_times, kwargs=dict(rid='770', series=1))
#        t.start()
####
#        t = Thread(target=self.analyze_count_times, kwargs=dict(rid='771', series=2))
#        t.start()

if __name__ == '__main__':
    d = CountAnalyzer()


    # d.configure_traits()
    x, y, _, _ = d.load_data('769')

    #    outlier_mask = zeros(len(x))
    step = 10
    m = zeros(step)
    end = len(x)
    end = 20
    for i in range(10, end, step):
    #    for i in range(10, 20, step):
    #    for i in [10, 10]:
    #        oom = outlier_mask[:i]
        d._detect_outliers_by_cluster(x[:i], y[:i], m)

        #        print m
        m = hstack((m, zeros(step)))
    #        print
    i = 1
    for xi, mi, oo in zip(x[:50], m[:50], d.omits[:50]):
        if mi:
            match = oo == 'User omitted'
        else:
            match = oo == 'OK'
        print i, xi, 'OK' if not mi else 'Omit', oo, match
        i += 1

    print sum(m), sum([1 if o == 'User omitted' else 0 for o in d.omits])
#======== EOF ================================
