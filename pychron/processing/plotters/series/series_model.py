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

# ============= local library imports  ==========================
from traits.api import on_trait_change, Dict

from pychron.processing.plotters.figure_model import FigureModel
from pychron.processing.plotters.series.series_panel import SeriesPanel, DashboardSeriesPanel


class SeriesModel(FigureModel):
    _panel_klass = SeriesPanel


class DashboardSeriesModel(SeriesModel):
    _panel_klass = DashboardSeriesPanel
    measurements = Dict

    @on_trait_change('measurements')
    def _measurements_changed(self):
        ps = self._make_panels()
        self.panels = ps
        self.panel_gen = (gi for gi in self.panels)

    def _make_panels(self):
        #key = lambda x: x.graph_id
        #ans = sorted(self.analyses, key=key)
        gs = self._panel_klass(measurements=self.measurements,
                               plot_options=self.plot_options,
                               group_id=0)
        #for gid, ais in groupby(ans, key=key)]

        return [gs, ]

    # ============= EOF =============================================
