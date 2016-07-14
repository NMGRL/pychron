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
from traits.api import Str, List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.models.figure_model import FigureModel
from pychron.pipeline.plot.panels.vertical_flux_panel import VerticalFluxPanel


class VerticalFluxModel(FigureModel):
    _panel_klass = VerticalFluxPanel
    irradiation = Str
    levels = List

    def _make_panels(self):
        panel = self._panel_klass(plot_options=self.plot_options,
                                  irradiation=self.irradiation,
                                  levels=self.levels)
        panel.make_figures()
        return [panel]

# ============= EOF =============================================
