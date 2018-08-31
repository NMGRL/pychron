# ===============================================================================
# Copyright 2016 ross
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
import csv
import os

from traits.api import Instance
from traitsui.api import View, UItem, VGroup

from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.diffusion_graph import DiffusionGraph


class MDDFigureEditor(BaseTraitsEditor):
    graph = Instance(DiffusionGraph)

    def __init__(self, *args, **kw):
        super(MDDFigureEditor, self).__init__(*args, **kw)

        self.root = '/Users/ross/Programming/github/pychron3/resources/lovera/bin/12H'
        self.replot()

    def data_path(self, name):
        return os.path.join(self.root, name)

    def _get_data(self, name, msg, func, delimiter=' '):
        path = self.data_path(name)
        if os.path.isfile(path):
            with open(path, 'r') as rfile:
                reader = csv.reader(rfile, delimiter=delimiter)
                return func(reader)
        else:
            self.warning('Cannot load {}. No file at {}'.format(msg, path))

    def _get_arrhenius_data(self, name='arr.samp'):
        def func(reader):
            inv_temp = []
            log_d = []
            for row in reader:
                if '&' not in row:
                    inv_temp.append(float(row[0]))
                    log_d.append(float(row[1]))

            return inv_temp, log_d

        return self._get_data(name, 'Arrhenius', func, '\t')

    def _get_cooling_history_data(self, name='confmed.dat'):
        def func(reader):
            age, low_conf, high_conf = [], [], []
            for row in reader:
                try:
                    age.append(float(row[0]))
                    low_conf.append(float(row[1]))
                    high_conf.append(float(row[2]))
                except ValueError:
                    continue
            return age, low_conf, high_conf

        return self._get_data(name, 'Cooling History', func)

    def _get_logr_ro_data(self, name='logr.samp'):
        def func(reader):
            logr = []
            logr39 = []
            for row in reader:
                if '&' not in row:
                    try:
                        logr.append(float(row[0]))
                        logr39.append(float(row[1]))
                    except ValueError:
                        continue

            return logr, logr39

        return self._get_data(name, 'Log R/Ro', func, '\t')

    def _get_spectrum_data(self, name='age.in'):
        def func(reader):
            a = []
            e = []
            for row in reader:
                row = [r for r in row if r != '']
                try:
                    e.append(float(row[0]))
                    a.append(float(row[1]))
                    e.append(float(row[0]))
                    a.append(float(row[1]))
                except ValueError:
                    pass
            return a, e

        def func2(reader):
            a = []
            e = []
            for row in reader:
                row = [r for r in row if r != '']
                try:
                    e.append(float(row[0]))
                    a.append(float(row[1]))
                except ValueError:
                    pass
            return a, e

        age, ar39 = self._get_data(name, 'Spectrum', func)
        age_err, ar39_err = self._get_data('age-sd.smp', 'Spectrum Errors', func2)

        return ar39[:-1], age[1:], ar39_err, age_err

    def _get_model_spectrum_data(self, name='ages-me.dat'):
        def func(reader):
            age = []
            ar39 = []
            for row in reader:
                try:
                    ar39.append(float(row[0]))
                    age.append(float(row[1]))
                except ValueError:
                    continue

            return ar39, age

        return self._get_data(name, 'Spectrum', func, '\t')

    def replot(self):
        graph = self.graph

        if graph is None:
            # panels = self.get_panels()
            # l = len(panels)
            # r = int(round(l / 2.0))
            # c = 1
            # if l > 2:
            #     c = 2
            r, c = 2, 2
            panels = ['panel_arrhenius', 'panel_arrhenius', 'panel_arrhenius', 'panel_arrhenius']
            graph = DiffusionGraph(include_panels=panels,
                                   container_dict=dict(
                                       kind='h' if c == 1 else 'g',
                                       bgcolor='white',
                                       padding=[10, 10, 40, 10],
                                       shape=(r, c)))
            graph.new_graph()

            for tag in ['arrhenius', 'cooling_history', 'logr_ro', 'spectrum']:
                data = getattr(self, '_get_{}_data'.format(tag))()
                if data is not None:
                    getattr(graph, 'build_{}'.format(tag))(*data)
        else:
            graph.clear()

        graph.refresh()
        self.graph = graph

    def traits_view(self):
        # ctrl_grp = VGroup(Item('use_weighted_mean'),
        #                   HGroup(Item('standard_ratio'),Item('current_yield')),
        #                   HGroup(Item('current'), UItem('revert_button')),
        #                   HGroup(Item('new_yield'), UItem('set_yield_button')))
        #
        # graph_grp = VGroup(UItem('graph', style='custom'))
        # v = View(VGroup(ctrl_grp, graph_grp))
        graph_grp = VGroup(UItem('graph', style='custom'))
        v = View(VGroup(graph_grp))
        return v

# ============= EOF =============================================
