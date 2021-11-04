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
# ============= standard library imports ========================
from numpy import array

# ============= local library imports  ==========================
from pychron.graph.ticks import IntTickGenerator
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure


class VerticalFlux(BaseArArFigure):
    def _setup_plot(self, i, pp, po):
        super(VerticalFlux, self)._setup_plot(i, pp, po)

        gen = IntTickGenerator()
        pp.y_axis.tick_generator = gen
        pp.y_grid.tick_generator = gen
        self.graph.set_x_title(self.options.x_title)

    def post_make(self):
        self.graph.set_x_limits(min_=self.xmi, max_=self.xma, pad="0.1")

    def plot(self, plots, legend=None):
        g = self.graph

        js, es, zs = self._gather_data()

        s, _ = g.new_series(js, zs, marker="circle", type="scatter")

        self._add_error_bars(s, es, "x", 2)

        g.set_y_limits(pad="0.1")

        # g.set_x_limits()
        es2 = es * 2
        self.xma = max(js + es2)
        self.xmi = min(js - es2)
        # self.xpad = '0.1'

    def _gather_data(self):
        return array([(i.j, i.j_err, i.z) for i in self.items]).T

        # js, es, zs = [], [], []
        # for i in self.items:
        #     js.append(i.j)
        #     es.append(i.j_err)
        #     zs.append(i.z)
        #
        # # for i, level in enumerate(self.levels):
        # #     p = os.path.join(paths.meta_root, self.irradiation,
        # #                      '{}.json'.format(level))
        # #     with open(p, 'r') as rfile:
        # #         obj = json.load(rfile)
        # #
        # #         positions = obj['positions']
        # #         d = next((o for o in positions if o['position'] == 1), None)
        # #         if d:
        # #             js.append(d['j'])
        # #             es.append(d['j_err'])
        # #             zs.append(obj.get('z', i))
        # return js, es, zs


# ============= EOF =============================================
