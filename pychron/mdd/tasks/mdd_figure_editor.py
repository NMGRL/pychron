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

from traits.api import Instance, List, HasTraits, Str, Event, Any, Bool, Color
from traitsui.api import View, UItem, VGroup
# from traitsui.editors import TreeEditor
from traitsui.tree_node import TreeNode

from pychron.core.ui.tree_editor import TreeEditor
from pychron.envisage.resources import icon
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.diffusion_graph import DiffusionGraph

visible = icon('eye')


class MDDItemNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        icon = visible if obj.visible else ''
        return icon


class BaseItem(HasTraits):
    name = Str
    enabled = Bool(True)


class MDDItem(BaseItem):
    plots = List
    background = Color
    visible = Bool(True)

    def toggle_visible(self):
        for p in self.plots:
            p.visible = not p.visible
            p.request_redraw()

        self.visible = p.visible
        self.background = 'white' if p.visible else 'lightgrey'


class MDDGraph(BaseItem):
    items = List(MDDItem)


class MDDTree(HasTraits):
    graphs = List(MDDGraph)

    def add_node(self, tag, name, plots):
        if plots is None:
            plots = []
            
        graph = self._get_graph(tag)
        if graph is None:
            graph = MDDGraph(name=tag)
            self.graphs.append(graph)

        graph.items.append(MDDItem(name=name, plots=plots))

    def _get_graph(self, tag):
        return next((g for g in self.graphs if g.name == tag), None)


class EditorOptions(HasTraits):
    tree = Instance(MDDTree, ())
    selected = Any
    dclicked = Event
    refresh_needed = Event

    def _dclicked_fired(self):
        self.selected.toggle_visible()
        self.refresh_needed = True

    def traits_view(self):
        nodes = [TreeNode(node_for=[MDDTree],
                          icon_open='',
                          children='graphs'),
                 TreeNode(node_for=[MDDGraph],
                          children='items',
                          label='name'),
                 MDDItemNode(node_for=[MDDItem],
                             label='name',
                             background='background')]
        v = View(UItem('tree', editor=TreeEditor(nodes=nodes,
                                                 hide_root=True,
                                                 editable=False,
                                                 refresh_icons='refresh_needed',
                                                 refresh='refresh_needed',
                                                 selected='selected',
                                                 dclick='dclicked')))
        return v


class MDDFigureEditor(BaseTraitsEditor):
    refresh_needed = Event
    graph = Instance(DiffusionGraph)
    roots = List
    editor_options = Instance(EditorOptions, ())
    plotter_options = Any

    def _refresh_needed_fired(self):
        self.replot(force=True)

    def _get_data(self, root, path, msg, func, delimiter=' '):
        path = os.path.join(root, path)
        if os.path.isfile(path):
            with open(path, 'r') as rfile:
                reader = csv.reader(rfile, delimiter=delimiter)
                return func(reader)
        else:
            self.warning('Cannot load {}. No file at {}'.format(msg, path))

    def _get_model_arrhenius_data(self, root):
        return self._get_arrhenius(root, 'arr.dat', 'Modeled Arrhenius')

    def _get_arrhenius_data(self, root):
        return self._get_arrhenius(root, 'arr.samp', 'Measured Arrhenius')

    def _get_arrhenius(self, root, name, tag):
        def func(reader):
            inv_temp = []
            log_d = []
            for row in reader:
                try:
                    inv_temp.append(float(row[0]))
                    log_d.append(float(row[1]))
                except ValueError:
                    continue

            return inv_temp, log_d

        return self._get_data(root, name, tag, func, '\t')

    def _get_cooling_history_data(self, root, name='confmed.dat'):
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

        return self._get_data(root, name, 'Cooling History', func, '\t')

    def _get_logr_ro_data(self, root, name='logr.samp'):
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

        return self._get_data(root, name, 'Log R/Ro', func, '\t')

    def _get_model_spectrum_data(self, root):
        return self._get_spectrum(root, 'ages-me.dat', 'Model Spectrum')

    def _get_spectrum_data(self, root):
        return self._get_spectrum(root, 'age.in', 'Spectrum')

    def _get_spectrum(self, root, name, tag):
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

        age, ar39 = self._get_data(root, name, tag, func)
        age_err, ar39_err = self._get_data(root, 'age-sd.smp', 'Spectrum Errors', func2)

        return ar39[:-1], age[1:], ar39_err, age_err

    def _get_model_spectrum_data(self, root, name='ages-me.dat'):
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

        return self._get_data(root, name, 'Spectrum', func, '\t')

    def replot(self, force=False):
        graph = self.graph
        if force:
            self.editor_options = EditorOptions()
            graph = None

        if graph is None:
            opt = self.plotter_options
            k, n, r, c = self.plotter_options.rc()
            graph = DiffusionGraph(container_dict=dict(kind=k,
                                                       bgcolor=opt.bgcolor,
                                                       # padding=[10, 10, 40, 10],
                                                       shape=(r, c)))
            ps = opt.panels()
            graph.new_graph(n, bgcolor=opt.plot_bgcolor, padding=opt.paddings())
            opt = self.editor_options
            for root in self.roots:
                for i, tags in ps:
                    for tag in tags:

                        ltag = tag.lower().replace(' ', '_')
                        data = getattr(self, '_get_{}_data'.format(ltag))(root)
                        if data is not None:
                            plots = getattr(graph, 'build_{}'.format(ltag))(*data, pid=i)
                            opt.tree.add_node(tag, os.path.basename(root), plots)
        else:
            graph.clear()

        graph.refresh()
        self.graph = graph

    def traits_view(self):
        graph_grp = VGroup(UItem('graph', style='custom'))
        v = View(VGroup(graph_grp))
        return v

# ============= EOF =============================================
