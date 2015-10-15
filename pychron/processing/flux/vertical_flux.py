# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, List, Instance
from traitsui.api import View, UItem, Controller
# ============= standard library imports ========================
import json
import os
# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.graph.graph import Graph
from pychron.graph.ticks import IntTickGenerator


class VerticalFluxModel(HasTraits):
    graph = Instance(Graph)
    irradiation = Str
    levels = List

    def load(self):
        self.graph = g = Graph()
        p = g.new_plot()

        js, es, zs = self._gather_data()
        g.new_series(js, zs,
                     marker='circle',
                     type='scatter')

        g.set_x_limits(pad='0.1')
        g.set_y_limits(pad='0.1')
        g.set_x_title('J')
        g.set_y_title('Z')

        gen = IntTickGenerator()
        p.y_axis.tick_generator = gen
        p.y_grid.tick_generator = gen

    def _gather_data(self):
        js, es, zs = [], [], []
        for i, level in enumerate(self.levels):
            p = os.path.join(paths.meta_root, self.irradiation,
                             '{}.json'.format(level))
            with open(p, 'r') as rfile:
                obj = json.load(rfile)
                d = next((o for o in obj if o['position'] == 1), None)
                if d:
                    js.append(d['j'])
                    es.append(d['j_err'])
                    zs.append(d.get('z', i))
        return js, es, zs


class VerticalFluxView(Controller):
    def traits_view(self):
        v = View(UItem('graph', style='custom'),
                 resizable=True)
        return v


if __name__ == '__main__':
    paths.build('_dev')
    m = VerticalFluxModel(irradiation='NM-258',
                          levels=['A', 'B', 'C', 'D'])
    m.load()
    v = VerticalFluxView(model=m)
    v.configure_traits()
# ============= EOF =============================================
