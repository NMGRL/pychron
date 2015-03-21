# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import HasTraits, Any, Int
from chaco.plot_containers import GridPlotContainer

from pychron.processing.plotters.graph_panel_info import GraphPanelInfo





# ============= standard library imports ========================
# ============= local library imports  ==========================

class FigureContainer(HasTraits):
    component = Any
    model = Any
    nrows = Int(1)
    ncols = Int(2)

    def _model_changed(self):

        gpi = GraphPanelInfo()

        self.model.refresh_panels()
        n = self.model.npanels
        comp, r, c = self._component_factory(n, gpi)
        for i in range(r):
            for j in range(c):
                try:
                    p = self.model.next_panel()
                except StopIteration:
                    break

                comp.add(p.make_graph())
                for ap in p.plot_options.aux_plots:
                    ap.clear_ylimits()
                    ap.clear_xlimits()

        self.component = comp

    def _component_factory(self, ngraphs, gpi):

        r = gpi.nrows
        c = gpi.ncols

        while ngraphs > r * c:
            if gpi.fixed == 'cols':
                r += 1
            else:
                c += 1

        if ngraphs == 1:
            r = c = 1

        op = GridPlotContainer(shape=(r, c),
                               bgcolor='white',
                               fill_padding=True,
                               use_backbuffer=True,
                               padding_top=0)
        return op, r, c


# ============= EOF =============================================
