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

from pychron.pipeline.plot.panels.figure_panel import FigurePanel
from pychron.pipeline.plot.plotter.dashboard_series import DashboardSeries
from pychron.pipeline.plot.plotter.series import Series
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.analysis_graph import AnalysisStackedRegressionGraph


class SeriesPanel(FigurePanel):
    _figure_klass = Series
    _graph_klass = AnalysisStackedRegressionGraph
    equi_stack = True
    # plot_spacing = 5
    use_previous_limits = False

    def _make_graph_hook(self, g):
        dma = 0
        for fig in self.figures:
            mi, ma = fig.get_data_x()
            dma = max(ma, dma)

        dmi = 0
        ma = 0
        for fig in self.figures:
            xs = fig.normalize(dma)

            dmi = min(dmi, min(xs))
            ma = max(ma, max(xs))

        g.set_x_limits(dmi, ma, pad=self.plot_options.xpadding or '0.1')
        for pid, p in enumerate(g.plots):

            ymi, yma = 0, 0
            for fig in self.figures:
                ys = p.data.get_data('y{}'.format(fig.group_id*2))
                # ys = fig.get_data_y(pid)
                ymi = min(ymi, min(ys))
                yma = max(yma, max(ys))

            g.set_y_limits(ymi, yma, pad='0.1', plotid=pid)
        g.refresh()


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
