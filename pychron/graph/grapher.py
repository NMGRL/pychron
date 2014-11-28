# ===============================================================================
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
# ===============================================================================



#=============enthought library imports=======================
from traits.api import HasTraits, Instance
from traitsui.api import View, Item

#============= standard library imports ========================
import argparse
import sys
import os
from numpy import loadtxt, histogram, zeros, ma
from pyface.timer.do_later import do_later
p = os.path.join(os.path.expanduser('~'), 'Programming', 'mercurial', 'pychron_beta1')

sys.path.append(p)
#============= local library imports  ==========================


class Grapher(HasTraits):
    graph = Instance(HasTraits)

    def _graph_default(self):
        return self._graph_factory()

    def _graph_factory(self):
        from pychron.graph.graph import Graph
        klass = Graph
        return klass()

    def traits_view(self):
        v = View(Item('graph', show_label=False, style='custom'),
                 resizable=True,
                 width=640,
                 height=480
                 )

        return v

    def load(self, datapath, kind):
        func = getattr(self, kind)
        data = loadtxt(datapath, delimiter=',', skiprows=1)
        func(data, datapath)

    def multi_line(self, data, path):
        g = self.graph
        g.new_plot()
        _r, c = data.shape
        for ci in range(0, c, 2):
            xs = data[:, ci]
            ys = data[:, ci + 1]
            g.new_series(xs, ys)


    def scatter(self, dataarr, datapath):
        g = self.graph
        g.new_plot(padding=[30, 10, 30, 30],
                   )

        _r, c = dataarr.shape
        for ci in range(0, c, 3):
            ages = ma.masked_equal(dataarr[:, ci], 0)
            errors = ma.masked_equal(dataarr[:, ci + 1], 0)
            k2o = ma.masked_equal(dataarr[:, ci + 2], 0)

            relative_errs = errors / ages * 100

            g.new_series(relative_errs, k2o, type='scatter', marker='circle')

        g.set_x_limits(0, max(relative_errs) * 1.1)
        g.set_y_limits(0, max(k2o) * 1.1)

        g.set_x_title('Relative Error (%)')
        g.set_y_title('K2O (%)')

    def hist(self, dataarr, path):
        g = self.graph

        '''
            input array
                g1iage,g1ierr,g2iage,g2ierr...
                .
                .
                .
                g1nage,...
        '''
#        dataarr = loadtxt(data, delimiter=',', skiprows=1)
        g.new_plot(padding=[30, 10, 30, 30],
                   show_legend='ur')
        r, c = dataarr.shape
        for ci in range(0, c, 2):
            ages = dataarr[:, ci]
            errs = dataarr[:, ci + 1]
            ages = ma.masked_equal(ages, 0)
            errs = ma.masked_equal(errs, 0)

            relative_errs = errs / ages * 100

            y, x = histogram(relative_errs)

            # convert edges to mids
            mids = zeros(len(x) - 1)
            for i in range(len(x) - 1):
                mids[i] = x[i] + (x[i + 1] - x[i]) / 2.0

            width = x[1] - x[0]

            g.new_series(mids, y, type='bar', bar_width=width)

        # add the labels
        with open(path, 'r') as f:
            header = f.readline()
            for i, l in enumerate(header.split(',')):
                g.set_series_label(l, series=i)
# ===============================================================================
#     hardcoded additions
# ===============================================================================
        g.set_x_title('Relative Error (%)')
        g.set_y_title('Frequency')


def do_grapher(args):
    op = args.o[0]
    g = Grapher()

    g.load(args.datafile[0], args.kind[0])
    if op:
        do_later(g.graph.save_pdf, op)

    g.configure_traits()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grapher')

    parser.add_argument('kind', metavar='kind', type=str, nargs=1)
    parser.add_argument('datafile', metavar='datafile', type=str, nargs=1)
    parser.add_argument('-o', metavar='outputpath', type=str, nargs=1)
    args = parser.parse_args()

    do_grapher(args)

#============= EOF =====================================
