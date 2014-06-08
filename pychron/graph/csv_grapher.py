# ===============================================================================
# Copyright 2012 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Instance, Button, Bool, List, Str, Property, Any, \
    Enum, File, Int
from traitsui.api import View, Item, EnumEditor, HGroup, ListEditor, InstanceEditor, Label, Spring, \
    VGroup, spring
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.timer.do_later import do_later
#============= standard library imports ========================
import numpy as np
import csv
import os
#============= local library imports  ==========================

from pychron.graph.graph import Graph
from pychron.graph.regression_graph import StackedRegressionGraph, RegressionGraph
from pychron.pychron_constants import FIT_TYPES, NULL_STR, DELIMITERS
from pychron.paths import paths
from pychron.loggable import Loggable
from pychron.core.time_series.time_series import smooth


class DataSelector(HasTraits):
    index = Str
    value = Str
    column_names = List
    parent = Any

    add_button = Button('+')
    remove_button = Button('-')
    removable = Bool(True)
    fit = Enum([NULL_STR] + FIT_TYPES)
    plot_type = Enum('line', 'scatter')
    use_filter = Bool(True)

    def traits_view(self):
        header = HGroup(Label('X'), Spring(width=60, springy=False),
                        Label('Y'), Spring(width=60, springy=False),
                        Label('Fit'), Spring(width=120, springy=False),
                        Label('Type'), Spring(width=80, springy=False),
                        Label('Filter'),
                        spring,
                        defined_when='not removable'
        )

        v = View(VGroup(header,
                        HGroup(
                            Item('index', editor=EnumEditor(name='column_names')),
                            Item('value', editor=EnumEditor(name='column_names')),
                            Item('fit'),
                            Item('plot_type'),
                            Item('use_filter'),
                            Item('add_button'),
                            Item('remove_button', defined_when='removable'),
                            show_labels=False
                        )
        ),
        )
        return v

    def _add_button_fired(self):
        self.parent.add_column_selector()

    def _remove_button_fired(self):
        self.parent.remove_column_selector(self)


class StatsGraph(HasTraits):
    graph = Instance(Graph)
    window_title = Str
    window_x = Int
    window_y = Int
    stats = Str
    sig_figs = Int(3)

    def _update_stats(self, new):
        self.stats = ''
        #        new = reversed(new)
        ss = ['{}. {}'.format(i + 1, ni.tostring(sig_figs=self.sig_figs)) for i, ni in enumerate(new)]
        self.stats = '\n'.join(ss)

    def _graph_changed(self):
        self.graph.on_trait_change(self._update_stats, 'regression_results')

    def traits_view(self):
        v = View(VGroup(
            Item('graph',
                 style='custom', show_label=False,
                 height=500, width=700),
            HGroup(
                Item('stats', show_label=False, style='readonly',
                     height=50,
                     width=1.0
                ),
                show_border=True,
                label='Stats',

            )
        ),
                 x=self.window_x,
                 y=self.window_y,
                 title=self.window_title,
                 resizable=True
        )
        return v


class CSVGrapher(Loggable):
    open_button = Button('Open')
    plot_button = Button('Plot')
    as_series = Bool(False)

    _path = Str
    path = File
    data_selectors = List
    column_names = List

    stats = Str
    file_name = Property(depends_on='_path')
    short_name = Property(depends_on='_path')

    _graph_count = 0
    delimiter = Str(',')

    def quick_graph(self, p):
        kind = 'scatter'
        #        for det in ['H2']:
        for det in ['H2', 'H1', 'AX', 'L1', 'L2']:
            g = self._gc(p, det, kind)
            info = g.edit_traits()
            g.save_pdf('/Users/argonlab2/Sandbox/baselines/auto-down50/{}_obama{}'.format(kind, det))
            #            info.dispose()

    def _gc(self, p, det, kind):
        g = Graph(container_dict=dict(padding=5),
                  window_width=1000,
                  window_height=800,
                  window_x=40,
                  window_y=20
        )
        with open(p, 'r') as fp:
            # gather data
            reader = csv.reader(fp)
            header = reader.next()
            groups = self._parse_data(reader)
            '''
                groups= [data,]
                data shape = nrow,ncols
                
            '''
            data = groups[0]
            x = data[0]
            y = data[header.index(det)]

        sy = smooth(y, window_len=120)  # , window='flat')

        x = x[::50]
        y = y[::50]
        sy = sy[::50]

        # smooth

        # plot
        g.new_plot(zoom=True, xtitle='Time (s)', ytitle='{} Baseline Intensity (fA)'.format(det))
        g.new_series(x, y, type=kind, marker='dot', marker_size=2)
        g.new_series(x, sy, line_width=2)
        #        g.set_x_limits(500, 500 + 60 * 30)
        #        g.edit_traits()
        return g

    def add_column_selector(self):
        csnames = self.column_names

        vind = len(self.data_selectors) + 1
        try:
            cs = self.data_selectors[-1].clone_traits(['fit', 'plot_type', 'parent'])
            cs.trait_set(index=csnames[0],
                         value=csnames[vind],
                         column_names=csnames)

            self.data_selectors.append(cs)
        except IndexError:
            self.warning_dialog('No More Columns')


    def remove_column_selector(self, cs):
        self.data_selectors.remove(cs)

    #===============================================================================
    # handlers
    #===============================================================================
    def _open_button_fired(self):
        self.data_selectors = []
        #        p = '/Users/ross/Sandbox/csvdata.txt'
        #        self._path = p
        #        self._path=os.path.join(paths.data_dir,'spectrometer_scans','scan007.txt')
        dlg = FileDialog(action='open', default_directory=paths.data_dir)
        if dlg.open() == OK:
            self._path = dlg.path

        with open(self._path, 'U') as fp:


            reader = csv.reader(fp, delimiter=self.delimiter)
            self.column_names = names = reader.next()
            try:
                cs = DataSelector(column_names=names,
                                  index=names[0],
                                  value=names[1],
                                  removable=False,
                                  parent=self,
                )
                self.data_selectors.append(cs)
            except IndexError:

                self.warning_dialog('Invalid delimiter {} for {}'.format(DELIMITERS[self.delimiter],
                                                                         os.path.basename(self._path)
                ))

    def _parse_data(self, reader):
        groups = []
        while 1:
            lines = []
            for l in reader:
                l = [li.strip() for li in l]
                if not l or not any(l):
                    data = np.array([map(float, l) for l in lines])
                    data = data.transpose()
                    groups.append(data)
                    break
                lines.append(l)
            else:
                #                print lines
                #                for l in lines:
                #                    print l
                #                    print map(float, l)
                #
                data = np.array([map(float, l) for l in lines])
                data = data.transpose()
                groups.append(data)
                break
        return groups


    def _plot_button_fired(self):
        with open(self._path, 'U') as fp:
            reader = csv.reader(fp, delimiter=self.delimiter)
            _header = reader.next()
            groups = self._parse_data(reader)
            #            print groups
            for data in groups:
                #                print data
                self._show_plot(data)

    def _show_plot(self, data):
        cd = dict(padding=5, stack_order='top_to_bottom')
        csnames = self.column_names
        xmin = np.Inf
        xmax = -np.Inf

        if self.as_series:
            g = RegressionGraph(container_dict=cd)
            p = g.new_plot(padding=[50, 5, 5, 50],
                           xtitle=''
            )
            p.value_range.tight_bounds = False
            p.value_range.margin = 0.1
        else:
            g = StackedRegressionGraph(container_dict=cd)

        regressable = False
        #        metadata = None
        for i, csi in enumerate(self.data_selectors):
            if not self.as_series:
                p = g.new_plot(padding=[50, 5, 5, 50])
                p.value_range.tight_bounds = False
                p.value_range.margin = 0.1
                plotid = i
            else:
                plotid = 0

            try:
                x = data[csnames.index(csi.index)]
                y = data[csnames.index(csi.value)]
                xmin = min(xmin, min(x))
                xmax = max(xmax, max(x))
                fit = csi.fit if csi.fit != NULL_STR else None
                g.new_series(x, y, fit=fit,
                             filter_outliers=csi.use_filter,
                             type=csi.plot_type,
                             plotid=plotid)

                g.set_x_title(csi.index, plotid=plotid)
                g.set_y_title(csi.value, plotid=plotid)
                if fit:
                    regressable = True

            except IndexError:
                pass

        g.set_x_limits(xmin, xmax, pad='0.1')

        self._graph_count += 1
        if regressable:
            gg = StatsGraph(graph=g)
            gii = gg
        else:
            gii = g

        g._update_graph()

        def show(gi):
            gi.window_title = '{} Graph {}'.format(self.short_name, self._graph_count)
            gi.window_x = self._graph_count * 20 + 400
            gi.window_y = self._graph_count * 20 + 20
            gi.edit_traits()

        show(gii)

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_file_name(self):
        if os.path.isfile(self._path):
            return os.path.relpath(self._path, paths.data_dir)
        else:
            return ''

    def _get_short_name(self):
        if os.path.isfile(self._path):
            return os.path.basename(self._path)
        else:
            return ''
            #===============================================================================
            # views
            #===============================================================================

    def traits_view(self):
        v = View(Item('as_series'), Item('delimiter', editor=EnumEditor(values=DELIMITERS)),
                 HGroup(Item('open_button', show_label=False),
                        Item('plot_button', enabled_when='_path', show_label=False),
                        Item('file_name', show_label=False, style='readonly')),
                 Item('data_selectors', show_label=False, editor=ListEditor(mutable=False,
                                                                            style='custom',
                                                                            editor=InstanceEditor())),


                 resizable=True,
                 width=525,
                 height=225,
                 title='CSV Plotter'
        )
        return v


if __name__ == '__main__':
    cs = CSVGrapher()
    #    cs.quick_graph('/Users/ross/Sandbox/scan007.txt')
    # do_later(cs.quick_graph, '/Users/ross/Sandbox/baselines/scan013.txt')
    #    do_later(cs.quick_graph, '/Users/ross/Sandbox/baselines/scan011.txt')
    do_later(cs.quick_graph, '/Users/argonlab2/Pychrondata/data/spectrometer_scans/scan017.txt')
    cs.configure_traits()
#============= EOF =============================================
