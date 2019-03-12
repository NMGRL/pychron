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
# ============= local library imports  ==========================
from pychron.pipeline.plot.models.figure_model import FigureModel
from pychron.pipeline.plot.panels.isochron_panel import InverseIsochronPanel
from pychron.pipeline.plot.panels.spectrum_panel import SpectrumPanel


class CompositeModel(FigureModel):

    # @on_trait_change('panels:figures:recalculate_event')
    # def _handle_recalculate(self):
    #     print('recalads')
    #     for p in self.panels:
    #         p.make_graph()

    # def _refresh_panels_hook(self):
    #     self.on_trait_change(self._handle_recalculate, 'panels:figures:recalculate_event')

    def _make_panels(self):

        # spo = SpectrumOptionsManager().selected_options
        # ipo = InverseIsochronOptionsManager().selected_options

        gs = [SpectrumPanel(analyses=self.analyses,
                            plot_options=self.plot_options.spectrum_options),
              InverseIsochronPanel(analyses=self.analyses,
                                   plot_options=self.plot_options.isochron_options)]
        for gi in gs:
            gi.make_figures()

        return gs

# ============= EOF =============================================
