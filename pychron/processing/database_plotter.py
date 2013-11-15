#===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
from traits.api import HasTraits, Str, Property, Instance, Button
from traitsui.api import View, Item, TableEditor, EnumEditor, HGroup, VGroup, Group
from pychron.graph.graph import Graph
#============= standard library imports ========================
#============= local library imports  ==========================

class DatabasePlotter(HasTraits):
    x = Str
    y = Str
    x_names = Property
    y_names = Property
    plot_button = Button('Plot')

    graph = Instance(Graph)
    def _plot_button_fired(self):
        self.graph.clear()

        self._plot()

    def _plot(self):
        g = self.graph
        g.new_plot(xtitle=self.x, ytitle=self.y)


        xs = [1, 2, 3, 4, 5, 6]
        ys = [1, 4, 9, 16, 25, 36]
        g.new_series(xs, ys)


    def _get_names(self):
        return ['A', 'B']

    def _get_x_names(self):
        return self._get_names()

    def _get_y_names(self):
        return self._get_names()

    def traits_view(self):
        ctrl_grp = VGroup(Item('x', editor=EnumEditor(name='x_names')),
                          Item('y', editor=EnumEditor(name='y_names')),
                          Item('plot_button', show_label=False)
                          )
        graph_grp = Group(Item('graph', style='custom', show_label=False))

        v = View(
                 HGroup(ctrl_grp, graph_grp),
                 resizable=True
                 )
        return v

    def _graph_default(self):
        klass = Graph
        g = klass(container_dict=dict(padding=5))
        return g
if __name__ == '__main__':
    dm = DatabasePlotter()
    dm.configure_traits()
#============= EOF =============================================
