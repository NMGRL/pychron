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

import logging

from chaco.plot_containers import GridPlotContainer, VPlotContainer
from traits.api import HasTraits, Any, Int
from pychron.graph.theme import themed_container_dict

logger = logging.getLogger(__name__)


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
        logger.debug(f"FigureContainer.refresh() called with clear={clear}, rows={self.rows}, cols={self.cols}")
        comp = self.component
        if clear and hasattr(comp, "components"):
            logger.debug("Clearing component.components")
            del comp.components[:]

        # Reset the panel generator before iterating, in case it was exhausted from a previous iteration
        if self.model and hasattr(self.model, 'reset_panel_gen'):
            self.model.reset_panel_gen()

        for i in range(self.rows):
            for j in range(self.cols):
                try:
                    p = self.model.next_panel()
                    logger.debug(f"Got panel at ({i}, {j}): {p}")
                except StopIteration:
                    logger.debug(f"No more panels at ({i}, {j})")
                    break

                graph = p.make_graph((i, self.rows), (j, self.cols))
                logger.debug(f"Adding graph from panel ({i}, {j}): {graph}")
                comp.add(graph)
                if clear and hasattr(p.plot_options, "aux_plots"):
                    for ap in p.plot_options.aux_plots:
                        ap.clear_ylimits()
                        ap.clear_xlimits()

        if hasattr(comp, "invalidate_and_redraw"):
            logger.debug("Calling comp.invalidate_and_redraw()")
            comp.invalidate_and_redraw()
        elif hasattr(comp, "request_redraw"):
            logger.debug("Calling comp.request_redraw()")
            comp.request_redraw()
        logger.debug("FigureContainer.refresh() complete")

    def model_changed(self, clear: bool = True, refresh_panels: bool = True) -> None:
        logger.debug(f"FigureContainer.model_changed() called with clear={clear}, refresh_panels={refresh_panels}")
        layout = self.model.plot_options.layout
        if refresh_panels:
            logger.debug("Calling model.refresh_panels()")
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
        logger.debug(f"Creating component with layout: npanels={n}, rows={r}, cols={c}")

        comp, r, c = self._component_factory(r, c)
        self.component = comp
        self.rows, self.cols = r, c
        logger.debug(f"Created component: {comp}, rows={r}, cols={c}")

        logger.debug("Calling refresh(clear={})".format(clear))
        self.refresh(clear=clear)
        logger.debug("FigureContainer.model_changed() complete")

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
