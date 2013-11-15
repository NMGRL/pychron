#!/usr/bin/python
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

#============= enthought library imports  ==========================
from traits.api import HasTraits, Instance, \
    Float, Str, List, Property, Button
from traitsui.api import View, Item, ListEditor, Group
#============= standard library imports  ==========================
import numpy as np


#============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.graph.time_series_graph import TimeSeriesStackedGraph
import os
import csv
from pychron.paths import paths
from pyface.file_dialog import FileDialog
from pyface.constant import OK

from pychron.viewable import Viewable
from collections import namedtuple

# DISPLAYSIZE = GetDisplaySize()
DISPLAYSIZE = namedtuple('Size', 'width height')(1000, 900)

class BakeoutParameters(HasTraits):
    setpoint = Float
    duration = Float
    max_output = Float
    script = Str
    name = Str
    script_text = Str
    view = View(
               Item('duration', style='readonly'),
               Item('setpoint', style='readonly'),
               Item('max_output', style='readonly'),
               Item('script', style='readonly'),
               Item('script_text', show_label=False, style='custom',
                    enabled_when='0')
                               )

    def __str__(self):
        s0 = '==== {} ===='.format(self.name)
        s1 = '\n'.join(['{:40s}= {:f}'.format(k, getattr(self, k))
         for k in ['duration', 'setpoint', 'max_output']])

        s2 = '{:40s}= {}'.format('script', self.script)

        return '\n'.join((s0, s1, s2, self.script_text))


# class BakeoutGraphViewer(Loggable):
class BakeoutGraphViewer(Viewable):
    graph = Instance(Graph)
    bakeouts = List
    summary = Property(depends_on='bakeouts')
    title = Str
    window_x = Float
    window_y = Float
    window_width = Float
    window_height = Float

    path = Str

#    export_button = Button('Export CSV')

#    def _export_button_fired(self):
    def export(self):
        self._export_csv()

    def _get_export_path(self):
        dlg = FileDialog(action='save as',
                         default_directory=paths.data_dir,
                         wildcard='CSV (*.csv, *.txt)|*.csv;*.txt'
                         )

        if dlg.open() == OK:
            p = dlg.path
            if not p.endswith('.csv'):
                if not p.endswith('.txt'):
                    p += '.csv'

            return p

    def _export_csv(self):
        if os.path.isfile(self.path):
            args = self._bakeout_h5_parser(self.path)
            data = args[3]
            names = args[0]

            op = self._get_export_path()
#            op = '/Users/ross/Desktop/exporttest.csv'
            if op is None:
                return

            self.info('exporting {} to {}'.format(self.title,
                                                  op))
            with open(op, 'w') as f:
                writer = csv.writer(f)
                ibs = args[2]
                j = 0
                ncols = 2 * sum(ibs)
                trows = []
                for d in data:
                    rows = zip(*d)
                    for k, ri in enumerate(rows):
                        try:
                            row = trows[k]
                        except IndexError:
                            row = ['', ] * (2 * sum(ibs) * args[1])

                        for i, rii in enumerate(ri):
                            row[i + j] = rii

                        try:
                            trows[k] = row
                        except IndexError:
                            trows.append(row)
                    j += ncols

                header = []
                for n in names:
                    header.append('{} time'.format(n))
                    for ib, ibn in zip(ibs, ['temp', 'heat', 'pressure']):
                        if ib:
                            header.append(ibn)

                writer.writerow(header)
                for row in trows:
                    writer.writerow(row)

    def _get_summary(self):
        s = '\n'.join([str(bi) for bi in self.bakeouts])
        return s

    def _bakeout_h5_parser(self, path):
        from pychron.managers.data_managers.h5_data_manager import H5DataManager
        dm = H5DataManager()
        if not dm.open_data(path):
            return

        controllers = dm.get_groups()
        datagrps = []
        attrs = []
        ib = [0, 0, 0]
        for ci in controllers:

            attrs_i = dict(name=ci._v_name)
            for ai in ['script', 'setpoint',
                        'duration', 'max_output',
                        'script_text']:
                attrs_i[ai] = getattr(ci._v_attrs, ai)
            attrs.append(attrs_i)
            data = []
            for i, ti in enumerate(['temp', 'heat']):
                try:
                    table = getattr(ci, ti)
                except Exception, _:
                    continue
                xs = [x['time'] for x in table]
#                    print 'xs', xs
                ys = [x['value'] for x in table]
                if i == 0:
                    data.append(xs)
                data.append(ys)
                ib[i] = 1
#                    print 'bakeout_manager._bakeout_h5_parser', e

            if data:
                datagrps.append(data)

        names = [ci._v_name for ci in controllers]
        nseries = len(controllers) * sum(ib)
        return names, nseries, ib, np.array(datagrps), path, attrs

    def _bakeout_csv_parser(self, path):
        attrs = None
        with open(path, 'r') as f:
#            reader = csv.reader(open(path, 'r'))
            reader = csv.reader(f)

            # first line is the include bits
            l = reader.next()
            l[0] = (l[0])[1:]
#
            ib = map(int, l)

            # second line is a header
            header = reader.next()
            header[0] = (header[0])[1:]
            nseries = len(header) / (sum(ib) + 1)
            names = [(header[(1 + sum(ib)) * i])[:-5] for i in range(nseries)]

#            average load time for 2MB file =0.42 s (n=10)
#            data = np.loadtxt(f, delimiter=',')

#            average load time for 2MB file = 0.19 s (n=10)
            data = np.array([r for r in reader], dtype=float)

            data = np.array_split(data, nseries, axis=1)
        return (names, nseries, ib, data, path, attrs)

    def load(self, path):
        self.path = path
        args = self._load_graph(path)
        if args:
            attrs = args[-1]
            for ai in attrs:
                bp = BakeoutParameters(**ai)
                self.bakeouts.append(bp)

    def _load_graph(self, path):
        _root, ext = os.path.splitext(path)
        ish5 = ext in ['.h5', '.hdf5']

        if ish5:
            args = self._bakeout_h5_parser(path)
        else:
            args = self._bakeout_csv_parser(path)

        if args is None:
            return
#        names = args[0]
#        attrs = args[-1]
        self.graph = self._bakeout_graph_factory(ph=0.65,
                *args,
                padding=[50, 10, 10, 50],
                transpose_data=not ish5

                )
        return args

    def _graph_factory(
        self,
        include_bits=None,
        panel_height=None,
        plot_kwargs=None,
        **kw
        ):

        if plot_kwargs is None:
            plot_kwargs = dict()

        if include_bits is None:
            include_bits = [self.include_temp, self.include_heat,
                            self.include_pressure]

        n = max(1, sum(map(int, include_bits)))
#        if graph is None:
        if panel_height is None:
            panel_height = DISPLAYSIZE.height * 0.65 / n

        graph = TimeSeriesStackedGraph(panel_height=panel_height,
                                        **kw)

        graph.clear()
        # kw['data_limit'] = self.scan_window * 60 / self.update_interval
        # kw['scan_delay'] = self.update_interval

        self.plotids = [0, 1, 2]

        # temps

        if include_bits[0]:
            graph.new_plot(show_legend='ll', zoom=True, **kw)
            graph.set_y_title('Temp (C)')
        else:
            self.plotids = [0, 0, 1]

        # heat power

        if include_bits[1]:
            graph.new_plot(**kw)
            graph.set_y_title('Heat Power (%)', plotid=self.plotids[1])
        elif not include_bits[0]:
            self.plotids = [0, 0, 0]
        else:
            self.plotids = [0, 0, 1]

        # pressure

#        if include_bits[2]:
#            graph.new_plot(**kw)
#            graph.set_y_title('Pressure (torr)', plotid=self.plotids[2])
#
#        if include_bits:
#            graph.set_x_title('Time')
#            graph.set_x_limits(0, self.scan_window * 60)

        return graph

    def _bakeout_graph_factory(
        self,
#        header,
        names,
        nseries,
        include_bits,
        data,
        path,
        attrs,
        ph=0.5,
        transpose_data=True,
        **kw
        ):

        ph = DISPLAYSIZE.height * ph / max(1, sum(include_bits))

        graph = self._graph_factory(stream=False,
                                    include_bits=include_bits,
                                    panel_height=ph,
                                    plot_kwargs=dict(pan=True, zoom=True),
                                     **kw)
        plotids = self.plotids
        for i, name in enumerate(names):
            for j in range(3):
                if include_bits[j]:
                    graph.new_series(plotid=plotids[j])
                    graph.set_series_label(name, series=i,
                                           plotid=plotids[j])

        ma0 = -1
        mi0 = 1e8
        ma1 = -1
        mi1 = 1e8
        ma2 = -1
        mi2 = 1e8
#        print data
        for (i, da) in enumerate(data):

            if transpose_data:
                da = np.transpose(da)

            x = da[0]
            if include_bits[0]:
                y = da[1]
                ma0 = max(ma0, max(y))
                mi0 = min(mi0, min(y))
                graph.set_data(x, series=i, axis=0, plotid=plotids[0])
                graph.set_data(da[1], series=i, axis=1,
                               plotid=plotids[0])
                graph.set_y_limits(mi0, ma0, pad='0.1',
                                   plotid=plotids[0])

            if include_bits[1]:
                y = da[2]
                ma1 = max(ma1, max(y))
                mi1 = min(mi1, min(y))
                graph.set_data(x, series=i, axis=0, plotid=plotids[1])
                graph.set_data(y, series=i, axis=1, plotid=plotids[1])
                graph.set_y_limits(mi1, ma1, pad='0.1',
                                   plotid=plotids[1])

            if include_bits[2]:
                y = da[3]
                ma2 = max(ma2, max(y))
                mi2 = min(mi2, min(y))
                graph.set_data(x, series=i, axis=0, plotid=plotids[2])
                graph.set_data(y, series=i, axis=1, plotid=plotids[2])
                graph.set_y_limits(mi2, ma2, pad='0.1',
                                   plotid=plotids[2])

                # prevent multiple pressure plots

                include_bits[2] = False

        graph.set_x_limits(min(x), max(x))
#        (name, _ext) = os.path.splitext(name)
#        graph.set_title(name)
        return graph

#    def new_controller(self, name):
#        bc = BakeoutParameters(name=name)
#        self.bakeouts.append(bc)
#        return bc
#
#    def traits_view(self):
#        bakeout_grp = Group(Item('bakeouts', style='custom',
#                             show_label=False,
#                             editor=ListEditor(use_notebook=True,
#                                                           dock_style='tab',
#                                                           page_name='.name'
#
#                                                           )),
# #                                layout='tabbed'
#                              )
#        graph_grp = Group(Item('graph', style='custom', show_label=False),
# #                       layout='tabbed'
#                       )
#        grp = Group(graph_grp, bakeout_grp, layout='tabbed')
# #        v = View(
# #                 graph_grp,
# #                 bakeout_grp,
# #                 resizable=True,
# #                 title=self.title,
# #                 x=self.window_x,
# #                 y=self.window_y,
# #                 width=self.window_width,
# #                 height=self.window_height
# #                 )
#        v = self.view_factory(grp)
#        return v

if __name__ == '__main__':
    d = BakeoutGraphViewer()
    p = '/Users/ross/Pychrondata1.4/data/bakeouts/2012/APR/bakeout-2012-04-02054.h5'
    d.load(p)
    d._export_csv()


# ============= EOF ====================================
