# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Event

# ============= standard library imports ========================
from pychron.pipeline.plot.panels.figure_panel import FigurePanel
from pychron.pipeline.plot.plotter.spectrum import Spectrum
# ============= local library imports  ==========================
from pychron.processing.analysis_graph import SpectrumGraph


class SpectrumPanel(FigurePanel):
    _graph_klass = SpectrumGraph
    _figure_klass = Spectrum
    make_ideogram_event = Event

    def _handle_make_ideogram(self):
        self.make_ideogram_event = [f.analysis_group for f in self.figures]

    def _get_init_xlimits(self):
        return None, 0, 100

    def _make_graph_hook(self, g):
        g.on_trait_change(self._handle_make_ideogram, 'make_ideogram_event')

# ============= EOF =============================================
