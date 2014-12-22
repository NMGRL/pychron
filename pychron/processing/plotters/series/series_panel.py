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
from traits.api import Dict, on_trait_change
# ============= standard library imports ========================
from pychron.processing.analysis_graph import AnalysisStackedRegressionGraph
from pychron.processing.plotters.series.dashboard_series import DashboardSeries
from pychron.processing.plotters.series.series import Series
from pychron.processing.plotters.figure_panel import FigurePanel

# ============= local library imports  ==========================


class SeriesPanel(FigurePanel):
    _figure_klass = Series
    equi_stack = True
    graph_klass = AnalysisStackedRegressionGraph
    plot_spacing = 5
    use_previous_limits = False


class DashboardSeriesPanel(SeriesPanel):
    _figure_klass = DashboardSeries
    measurements = Dict

    @on_trait_change('measurements')
    def _analyses_items_changed(self):
        self.figures = self._make_figures()

    def _make_figures(self):
        gs = [self._figure_klass(measurements=self.measurements), ]
        return gs

    # ============= EOF =============================================
