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
    def _make_panels(self):
        spo = self.plot_options.get_options('spectrum')
        ipo = self.plot_options.get_options('inverseisochron')
        gs = [SpectrumPanel(analyses=self.analyses,
                            plot_options=spo),
              InverseIsochronPanel(analyses=self.analyses,
                                   plot_options=ipo)]

        return gs

# ============= EOF =============================================
