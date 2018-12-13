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
from __future__ import absolute_import
from chaco.plot_containers import GridPlotContainer, VPlotContainer
from traits.api import HasTraits, Any, Int
# from pychron.processing.plotters.graph_panel_info import GraphPanelInfo
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.codetools.inspection import caller


class FigureContainer(HasTraits):
    component = Any
    model = Any

    # nrows = Int(1)
    # ncols = Int(2)
    rows = Int
    cols = Int

    @caller
    def refresh(self, clear=False):
        comp = self.component
        for i in range(self.rows):
            for j in range(self.cols):
                try:
                    p = self.model.next_panel()
                except StopIteration:
                    break

                comp.add(p.make_graph())
                if clear and hasattr(p.plot_options, 'aux_plots'):
                    for ap in p.plot_options.aux_plots:
                        ap.clear_ylimits()
                        ap.clear_xlimits()

    def model_changed(self, clear=True):
        layout = self.model.plot_options.layout
        self.model.refresh_panels()
        n = self.model.npanels

        comp, r, c = self._component_factory(n, layout)
        self.component = comp
        self.rows, self.cols = r, c

        self.refresh(clear=clear)

    def _model_changed(self):
        self.model_changed(True)

    def _component_factory(self, ngraphs, layout):
        r, c = layout.calculate(ngraphs)

        op = GridPlotContainer(shape=(r, c),
                               bgcolor='white',
                               fill_padding=True,
                               use_backbuffer=True,
                               padding_top=0)
        return op, r, c

    def _component_default(self):
        return VPlotContainer()

# ============= EOF =============================================
