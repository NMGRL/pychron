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
import copy

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.models.figure_model import FigureModel
from pychron.pipeline.plot.panels.isochron_panel import InverseIsochronPanel
from pychron.pipeline.plot.panels.spectrum_panel import SpectrumPanel


class CompositeModel(FigureModel):
    def _make_panel_groups(self):
        # do to a quirk in how ArArFigure.build is handling columns we need to artifically double the fixed width
        # for the options layout
        specopts = copy.deepcopy(self.plot_options.spectrum_options)
        specopts.layout.fixed_width *= 2

        isoopts = copy.deepcopy(self.plot_options.isochron_options)
        isoopts.layout.fixed_width *= 2

        gs = [
            SpectrumPanel(analyses=self.analyses, plot_options=specopts),
            InverseIsochronPanel(analyses=self.analyses, plot_options=isoopts),
        ]
        return gs

    def _make_panels(self):
        gs = super(CompositeModel, self)._make_panels()
        if self.plot_options.auto_generate_title:
            for gi in gs:
                gi.title = ""

        else:
            for i, gi in enumerate(gs):
                if gi.plot_options.auto_generate_title:
                    gi.title = gi.plot_options.generate_title(gi.analyses, i)

        return gs


# ============= EOF =============================================
