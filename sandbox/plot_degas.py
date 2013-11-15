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



#=============enthought library imports=======================
from traits.api import HasTraits, Button
from traitsui.api import View, Item
from pychron.graph.graph import Graph
from pychron.paths import paths
import os
from pychron.graph.time_series_graph import TimeSeriesStackedGraph
from pychron.managers.manager import Manager
#============= standard library imports ========================
#============= local library imports  ==========================

DEGAS = os.path.join(paths.data_dir, 'degas')


class DegasViewer(Manager):
    open = Button
    build = Button

    def _build_fired(self):
        self.build_graphs()

    def _open_fired(self):
        p = self.open_file_dialog(default_directory=DEGAS)
        self.open_graph(p)

    def traits_view(self):
        return View(
            Item('open', show_label=False),
            Item('build', show_label=False),
            resizable=True)

    def open_graph(self, p, save=False, offset=(0, 0)):
        g = TimeSeriesStackedGraph(panel_height=190)
        x = []
        sp = []
        ion = []
        temp = []
        with open(p, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                line = line.split(',')
                try:
                    x.append(float(line[0]))
                    sp.append(float(line[1]))
                    ion.append(float(line[2]))
                    temp.append(float(line[3]))
                except ValueError:
                    print p
                    return

        g.new_plot()
        g.new_series(x, sp)
        g.set_y_limits(max=max(sp) + 5)
        g.set_x_title('Time')
        g.set_y_title('Setpoint')

        g.new_plot()
        g.new_series(x, ion, plotid=1, value_scale='log')
        g.set_y_title('Pressure (torr)', plotid=1)
        g.plots[1].value_axis.tick_label_formatter = lambda x: '{:0.2e}'.format(x)

        g.new_plot()
        g.new_series(x, temp, plotid=2)
        g.set_y_title('Temp (C)', plotid=2)

        g.window_height = 780
        g.window_title = os.path.basename(p)
        g.window_x = 50 + offset[0]
        g.window_y = 50 + offset[1]
        g.set_title(os.path.basename(p))

        g.edit_traits()
        if save:
            name, ext = os.path.splitext(os.path.basename(p))
            p = os.path.join(DEGAS, '{}.png'.format(name))
            g.save_png(p)

    def build_graphs(self):
        i = 0
        for p in os.listdir(DEGAS):
            if p.startswith('scan'):
                self.open_graph(os.path.join(DEGAS, p), save=True, offset=(15 * i, 5 * i))
                i += 1


def main():
    dg = DegasViewer()
    dg.configure_traits()


if __name__ == '__main__':
    main()
#============= EOF =====================================

