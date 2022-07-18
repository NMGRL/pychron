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

    # make_alternate_figure_event = Event

    def _handle_figure_event(self, new):
        kind = new[0]
        if kind == "alternate_figure":
            self.figure_event = (kind, new[1], [f.analysis_group for f in self.figures])
        elif kind == "tag":
            self.figure_event = (
                "tag",
                [
                    a
                    for f in self.figures
                    for a in f.analysis_group.analyses
                    if not f.analysis_group.get_is_plateau_step(a)
                ],
            )

    def _get_init_xlimits(self):
        return None, 0, 100

    def _make_graph_hook(self, g):
        g.on_trait_change(self._handle_figure_event, "figure_event")

    def _handle_rescale(self, obj, name, new):
        if new == "y":
            plotid = obj.selected_plotid
            for f in self.figures:
                ma, mi = f.get_ybounds(plotid)
            obj.set_y_limits(mi, ma, pad="0.025", plotid=plotid)
        # elif new == 'valid':
        #     l, h = None, None
        #     for f in self.figures:
        #         ll, hh = f.get_valid_xbounds()
        #         if l is None:
        #             l, h = ll, hh
        #
        #         l = min(l, ll)
        #         h = max(h, hh)
        #
        #     obj.set_x_limits(l, h)
        #
        # elif new == 'x':
        #     center, xmi, xma = self._get_init_xlimits()
        #     obj.set_x_limits(xmi, xma)
        #     for f in self.figures:
        #         f.replot()


# ============= EOF =============================================
