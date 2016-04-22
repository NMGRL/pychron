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
# ============= standard library imports ========================
from pychron.pipeline.plot.panels.figure_panel import FigurePanel
from pychron.pipeline.plot.plotter.xy_scatter import XYScatter
from pychron.processing.analysis_graph import AnalysisStackedRegressionGraph


# ============= local library imports  ==========================


class XYScatterPanel(FigurePanel):
    _figure_klass = XYScatter
    _graph_klass = AnalysisStackedRegressionGraph
    equi_stack = True
    # plot_spacing = 5
    use_previous_limits = False

    def _make_graph_hook(self, g):
        g.refresh()

# ============= EOF =============================================
