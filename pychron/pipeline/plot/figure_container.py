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
from pychron.graph.theme import themed_container_dict


# from pychron.processing.plotters.graph_panel_info import GraphPanelInfo
# ============= standard library imports ========================
# ============= local library imports  ==========================


class FigureContainer(HasTraits):
    component = Any
    model = Any

    # nrows = Int(1)
    # ncols = Int(2)
    rows = Int
    cols = Int

    def refresh(self, clear: bool = False) -> None:
        comp = self.component
        if clear and hasattr(comp, "components"):
            del comp.components[:]

        for i in range(self.rows):
            for j in range(self.cols):
                try:
                    p = self.model.next_panel()
                except StopIteration:
                    break

                comp.add(p.make_graph((i, self.rows), (j, self.cols)))
                if clear and hasattr(p.plot_options, "aux_plots"):
                    for ap in p.plot_options.aux_plots:
                        ap.clear_ylimits()
                        ap.clear_xlimits()

        if hasattr(comp, "invalidate_and_redraw"):
            comp.invalidate_and_redraw()
        elif hasattr(comp, "request_redraw"):
            comp.request_redraw()

    def model_changed(self, clear: bool = True, refresh_panels: bool = True) -> None:
        layout = self.model.plot_options.layout
        if refresh_panels:
            self.model.refresh_panels()
        if hasattr(self.model.plot_options, "orientation_layout"):
            if self.model.plot_options.orientation_layout == "Vertical":
                layout.fixed = "column"
                layout.columns = 1
            else:
                layout.fixed = "row"
                layout.rows = 1

        n = self.model.npanels
        r, c = layout.calculate(n)

        comp, r, c = self._component_factory(r, c)
        self.component = comp
        self.rows, self.cols = r, c

        self.refresh(clear=clear)

    def _model_changed(self) -> None:
        self.model_changed(True)

    def _component_factory(self, r: int, c: int):
        op = GridPlotContainer(
            shape=(r, c),
            use_backbuffer=True,
            padding_top=0,
            **themed_container_dict(),
        )
        return op, r, c

    def _component_default(self) -> VPlotContainer:
        return VPlotContainer()


# ============= EOF =============================================
