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
from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.iterfuncs import groupby_group_id
from pychron.envisage.view_util import open_view
from pychron.graph.regression_graph import RegressionGraph
from pychron.options.layout import filled_grid
from pychron.pipeline.plot.panels.figure_panel import FigurePanel
from pychron.processing.analysis_graph import ReferencesGraph


class ReferencesPanel(FigurePanel):
    references = List
    _graph_klass = ReferencesGraph

    def _handle_make_correlation_event(self, evt):
        refplot, xtitle = evt

        fi = self.figures[0]

        n = len(list(fi.options.get_plotable_aux_plots()))
        plots = list(reversed(fi.graph.plots))

        xs = refplot.data.get_data('y1')

        r, c = filled_grid(n - 1)
        g = RegressionGraph(container_dict={'kind': 'g', 'shape': (r, c)}, window_title='Correlation')
        i = 0
        for pp in plots:
            ytitle = pp.y_axis.title
            if ytitle == xtitle:
                continue

            g.new_plot(xtitle=xtitle, ytitle=ytitle, padding=[80, 10, 10, 40])
            ys = pp.data.get_data('y1')
            g.new_series(xs, ys, fit='linear', use_error_envelope=False, plotid=i)
            g.add_correlation_statistics(plotid=i)

            g.set_x_limits(pad='0.1', plotid=i)
            g.set_y_limits(pad='0.1', plotid=i)
            i += 1

        g.refresh()

        open_view(g)

    def _make_graph_hook(self, g):
        g.on_trait_change(self._handle_make_correlation_event, 'make_correlation_event')

    def _make_figures(self):
        gs = super(ReferencesPanel, self)._make_figures()

        gg = groupby_group_id(self.references)
        for gi in gs:
            try:
                _, refs = next(gg)
                gi.references = list(refs)
            except StopIteration:
                break

        return gs

# ============= EOF =============================================
