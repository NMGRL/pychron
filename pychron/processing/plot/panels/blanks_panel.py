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
from itertools import groupby

from pychron.processing.analysis_graph import AnalysisStackedRegressionGraph
from pychron.processing.plot.panels.figure_panel import FigurePanel
from pychron.processing.plot.plotter.blanks import Blanks


class BlanksPanel(FigurePanel):
    _figure_klass = Blanks
    graph_klass = AnalysisStackedRegressionGraph

    def _make_figures(self):
        gs = super(BlanksPanel, self)._make_figures()

        key = lambda x: x.group_id
        refs = sorted(self.references, key=key)
        gg = groupby(refs, key=key)
        for gi in gs:
            _, refs = gg.next()
            gi.references = list(refs)

        return gs
# ============= EOF =============================================
