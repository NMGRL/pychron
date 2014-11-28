## ===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
## ===============================================================================
#
#
#
##=============enthought library imports=======================
# from traits.api import HasTraits, File, Str, Bool, Event, Enum, Button, \
#    String, Property, List, Int, Any, Directory
# from traitsui.api import View, Item, HGroup, spring, TableEditor, ButtonEditor
# from traitsui.extras.checkbox_column import CheckboxColumn
# from traitsui.table_column import ObjectColumn
# from pyface.message_dialog import information
#
#
##=============standard library imports ========================
# import os
# import csv
# import numpy as np
# from threading import Thread
##=============local library imports  ==========================
# from manager import Manager
# from pychron.data_processing.import_filters.qtegra_filter import QtegraFilter
# from pychron.paths import paths
# from pychron.graph.regression_graph import RegressionGraph
# from pychron.data_processing.regression.regressor import Regressor
# from pychron.core.helpers.filetools import unique_path
# from pychron.core.helpers.data_tools import add_sub_error_prop#, mult_div_error_prop
#
# class RegressionItem(HasTraits):
#    fit_type = Enum('linear', 'parabolic', 'average +/- SD', 'average +/- SEM', 'cubic', 'exponential')
#    name = String
#    data_path = String
#    export = Bool(True)
#    _regressor = Regressor()
#
#    def do_fit(self):
#        reg = self._regressor
#        fit_type = self.fit_type
#        kw = dict()
#        if 'average' in fit_type:
#            kw['use_stderr'] = True if 'SEM' in fit_type else False
#            fit_type = 'average'
#
#        #x, y, er = self.get_data()
#        data = self.get_data()
#        rfunc = getattr(reg, fit_type)
#        rdict = rfunc(*data[:2], **kw)
#
#        self.intercept = rdict['coefficients'][-1]
#        self.intercept_error = rdict['coeff_errors'][-1]
#
#    def get_data(self):
#        data = np.loadtxt(self.data_path, delimiter='\t', skiprows=1)
#        xs, ys, ers = np.hsplit(data, 3)
#        return xs.flatten(), ys.flatten(), ers.flatten()
#
#    def get_result_row(self):
#        return [self.intercept, self.intercept_error, self.intercept_error / self.intercept * 100]
#
# class PeakRegressionManager(Manager):
#    fitall = Enum('linear', 'parabolic', 'average +/- SD', 'average +/- SEM', 'cubic', 'exponential')
#    exportbutton = Button('Export')
#
#    exportall = Event
#    exportall_str = Property(depends_on='_export_all')
#    _export_all = Bool(True)
#    import_button = Button('Import')
#
#    name = Str# Property(depends_on = 'path')
#    path = File
#
#    results = List
#    directory = Directory(os.path.join(paths.data_dir, 'sandbox'))
#    ndetectors = Int(2)
#    selected = Any
#
#
#
#    def _get_exportall_str(self):
#        return 'Export All' if not self._export_all else 'Export None'
#
#    def _get_grouped_results(self):
#
#        groups = [[]]
#        for r in self.results:
#            #the first two chars of the name represent the run number
#            try:
#                rid = int(r.name[:3])
#            except ValueError:
#                rid = int(r.name[:2])
#
#            if len(groups) == rid:
#                groups[rid - 1].append(r)
#            else:
#                groups.append([r])
#
#        #sort the groups by mass
#        ngroups = []
#        for items in groups:
#            names = [ri.name.split('_')[1] for ri in items]
#
#            master = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
#            #match items to the master
#            ngroup = range(len(master))
#            tx = range(len(master))
#            for i, name in enumerate(names):
#                ind = master.index(name)
#                item = items[i]
#                if not isinstance(ngroup[ind], int):
#                    ngroup.insert(ind, item)
#                else:
#                    ngroup[ind] = item
#                    tx[ind] = item.name
#
#            #compress ngroup
#            ngroup = [n for n in ngroup if not isinstance(n, int)]
#
#            ngroups.append(ngroup)
#
#        #self.names = ['_'.join(n.name.split('_')[1:]) for n in ngroup]
#
#        return ngroups
#
#    def _exportbutton_fired(self):
#        t = Thread(target=self._export_results)
#        t.start()
#
#    def _export_results(self):
#        #get a new path for the fit results
#        #file numbers auto  incremented
#        #located the current directory
#
#        p, _cnt = unique_path(os.path.splitext(self.path)[0],
#                              'fit_results',
#                              extension='csv')
#
#        if p is not None:
#
#            #write as binary file for windows compatibilty
#            with open(p, 'wb') as f:
#                writer = csv.writer(f)
#
#                #build header rows
#                headera = [' ']
#                headerb = ['Run#']
#
#                gs = self._get_grouped_results()
#
#                ga = gs[0]
#                for ri in ga:
#                    #trim off the runid
#                    ti = 4
#                    if ri.name[3] != '_':
#                        ti = 3
#                    headera += [ri.name[ti:], ' ', ' ']
#                    headerb += ['intercept', 'intercept err', 'intercept err %']
#
#                #write a header rows
#                writer.writerow(headera)
#                writer.writerow(headerb)
#
#                #get the fit results
#                #loop thru each group ie Run
#                data = []
#                for i, gi in enumerate(gs):
#                    row = []
#                    for ri in gi:
#                        if ri.export:
#                            ri.do_fit()
#                            row += ri.get_result_row()
#
#                    #store fit results to calc stats
#                    data.append(row)
#                    writer.writerow([i + 1] + row)
#
#                #calculate fit stats
#                data = np.array(data)
#                data = np.transpose(data)
#
#                statsrow = [' ']
#                statsheader = ['stats']
#
#                for i in range(0, np.shape(data)[0], 3):
#                    ds = data[i]
#                    es = data[i + 1]
#                    #propagate summed error
#                    #error = reduce(lambda a, b: (a ** 2 + b ** 2) ** 0.5, es)
#                    error = add_sub_error_prop(es)
#                    statsrow += [np.mean(ds), error, ' ']
#                    statsheader += ['mean', 'error', ' ']
#
#                writer.writerow([])
#                writer.writerow(statsheader)
#                writer.writerow(statsrow)
#
#        msg = 'Fit results location\n%s' % p
#        information(None, msg, 'Export')
#
#    def _exportall_fired(self):
#
#        if self.results:
#            self._export_all = not self._export_all
#            for r in self.results:
#                r.export = self._export_all
#
#    def _fitall_changed(self):
#        if self.results:
#            for r in self.results:
#                r.fit_type = self.fitall
#
#    def _selected_changed(self):
#        if self.selected is not None:
#            self._open_graph(self.selected[0])
#
#    def _open_graph(self, item):
#
#        #xs, ys, ers = item.get_data()
#        data = item.get_data()
#        g = RegressionGraph(window_title=item.name,
#                            window_width=800,
#                            window_height=700,
#                            container_dict=dict(padding=10)
#                            )
#
#        g.new_plot(padding=[50, 5, 5, 30])
#        g.set_x_title('Time (sec)')
#        g.set_y_title('Intensity (fA)')
#
#        g.new_series(x=data[0].flatten(), y=data[1].flatten(), type='scatter', marker='circle', marker_size=3)
#        g.set_x_limits(min=0)
#        g.edit_traits(parent=self.ui.control)
#
#    def _get_name(self):
#        if self.path:
#            return os.path.basename(self.path)
#        else:
#            return ''
#
#    def _path_changed(self):
#        self.name = self.name_factory(self.path)
#        self.do_import()
#
#    def name_factory(self, path):
#        root = os.path.basename(path)
#        args = os.path.splitext(root)
#
#        return args[0]
#
#    def _directory_changed(self):
#        self.load_directory()
#
#    def load_directory(self):
#        files = os.listdir(self.directory)
#        self.trait_set(
#                       path=self.directory,
#                       trait_change_notify=False)
#        self.name = self.name_factory(self.directory)
#
#        self.results = self._results_factory([os.path.splitext(f)[0] for f in files])
#
#    def _results_factory(self, results):
#        rs = []
#
#        argsn = os.path.splitext(self.name)
#        argsp = os.path.split(self.path)
#        for ri in results:
#            #ignore files that dont start with a number
#            try:
#                int(ri[:2])
#            except ValueError:
#                continue
#
#            path = os.path.join(argsp[0], argsn[0], '%s.txt' % ri)
#
#            ra = RegressionItem(name=ri,
#                           data_path=path,
#                           fit_type=self.fitall
#                           )
#            rs.append(ra)
#        return rs
#
#    def do_import(self):
#        p = self.path
#        if p:
#
#            kw = dict(#'with_results'=self.with_results,
#                    nisotopes=self.ndetectors
#                    )
#            f = self._filter_factory(**kw)
#            results = f.filter(p)
#
#            if results:
#                self.results = self._results_factory(results)
#            else:
#                self.path = ''
#
#    def _filter_factory(self, **kw):
#        imf = QtegraFilter(**kw)
#
#        return imf
#
#    def traits_view(self):
#        cols = [ObjectColumn(name='name', width=0.25, editable=False),
#              CheckboxColumn(name='export'),
#              ObjectColumn(name='fit_type', width=0.6)
#              ]
#
#        v = View(
#
#               Item('name',
#                    style='readonly',
#                    show_label=False
#                    ),
#               Item('results', show_label=False,
#                   editor=TableEditor(columns=cols,
#                                        auto_size=False,
#                                        dclick='selected'
#                                        )
#                   ),
#               HGroup(Item('exportall', editor=ButtonEditor(label_value='exportall_str'),
#                            show_label=False),
#                      Item('exportbutton', show_label=False),
#                      Item('fitall', label='Fit All'),
#                      enabled_when='results'
#                      ),
#
#               Item('directory', label='Load'),
#               HGroup(Item('ndetectors', label='Num Detectors'), spring),
#               Item('path', label='Import'),
#
#               title='Peak Regression Manager',
#               resizable=True,
#               width=600,
#               height=400,
#               handler=self.handler_klass
#               )
#        return v
#
# def main():
#    i = PeakRegressionManager()
#    i.configure_traits()
#
# def main2():
#    from pychron.data_processing.regression.ols import OLS
#    path = '/Users/Ross/Pychrondata_beta/data/sandbox/West Air CDD w 36 ax labbook 2/4_H1_40.txt'
#    xs = []
#    ys = []
#    with open(path, 'r') as f:
#        reader = csv.reader(f, delimiter='\t')
#        reader.next()
#
#        for r in reader:
#
#            xs.append(float(r[0]))
#            ys.append(float(r[1]))
#    o = OLS(xs, ys, fitdegree=2)
#    print o.get_coefficients()
#    print o.get_coefficient_standard_errors()
#
#    #print o.results.summary()
#
#
# #def main3():
# #    from pychron.data_processing.regression.regressor import Regressor
# #
# #    regressor = Regressor()
# #    path = '/Users/fargo2/Pychrondata_beta/data/sandbox/April 4 Axial 4036 labbook 1/5_AX_40.txt'
# #    xs = []
# #    ys = []
# #    with open(path, 'r') as f:
# #        reader = csv.reader(f, delimiter = '\t')
# #        header = reader.next()
# #        for r in reader:
# #
# #            xs.append(float(r[0]))
# #            ys.append(float(r[1]))
# #
# #
# #    ff = lambda p, x:p[0] * np.exp(p[1] * x)
# #    ef = lambda p, x, y: ff(p, x) - y
# #    r = regressor.least_squares(xs, ys, fitfunc = ff, errfunc = ef, p0 = [1, -1])
# def test():
#    pm = PeakRegressionManager()
# #    pm.directory = '/Users/Ross/Pychrondata_beta/data/sandbox/West Air CDD w 36 ax labbook 2'
#    #pm.directory = '/Users/fargo2/Pychrondata_beta/data/sandbox/April 11 Faraday air labbook'
#    pm.directory = '/Users/fargo2/Pychrondata_beta/data/sandbox/test'
#    pm.load_directory()
#    #print pm._get_grouped_results()
#    pm._exportbutton_fired()
#
#
# if __name__ == '__main__':
#    #main()
#    test()
#
#
##============= EOF ====================================
#
#
