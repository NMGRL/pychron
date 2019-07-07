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
from __future__ import absolute_import
from traits.api import on_trait_change, Dict

from pychron.pipeline.plot.models.figure_model import FigureModel
# from pychron.processing.plot.panels.series_panel import SeriesPanel, DashboardSeriesPanel
from pychron.pipeline.plot.panels.regression_series_panel import RegressionSeriesPanel
from pychron.pipeline.plot.panels.series_panel import SeriesPanel, DashboardSeriesPanel
from six.moves import zip


class RegressionSeriesModel(FigureModel):
    _panel_klass = RegressionSeriesPanel

    def _make_panels(self):
        gs = [self._panel_klass(analyses=[a], plot_options=self.plot_options) for a in self.analyses]
        for gi in gs:
            gi.make_figures()

        if self.plot_options.auto_generate_title:
            for i, gi in enumerate(gs):
                gi.title = self.plot_options.generate_title(gi.analyses, i)

        elif self.titles:
            for ti, gi in zip(self.titles, gs):
                gi.title = ti

        return gs

# ============= EOF =============================================
