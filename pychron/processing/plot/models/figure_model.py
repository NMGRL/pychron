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
from traits.api import HasTraits, List, Property, Any, Instance
# ============= standard library imports ========================
from itertools import groupby
# ============= local library imports  ==========================
from pychron.processing.plot.layout import FigureLayout


class FigureModel(HasTraits):
    panels = List
    npanels = Property(depends_on='panels[]')
    analyses = List
    references = List
    plot_options = Any
    _panel_klass = Instance('pychron.processing.plotters.figure_panel.FigurePanel')
    titles = List

    layout = Instance(FigureLayout, ())
    analysis_groups = List

    def refresh(self, force=False):
        if not self.panels or force:
            self.refresh_panels()

        for p in self.panels:
            print 'p', p.figures
            if not p.figures or force:
                p.make_graph()

            for f in p.figures:
                f.replot()

    def dump_metadata(self):
        ps = []

        for pp in self.panels:
            ps.append(pp.dump_metadata())

        return ps

    def load_metadata(self, metadata):
        for pp, meta in zip(self.panels, metadata):
            pp.load_metadata(meta)

    # @on_trait_change('analyses[]')
    # def _analyses_items_changed(self):
    #     self.refresh_panels()

    def refresh_panels(self):
        ps = self._make_panels()
        self.panels = ps
        self.panel_gen = (gi for gi in self.panels)

    def _make_panels(self):
        if self.analysis_groups:
            gs = [self._panel_klass(analyses=ag, plot_options=self.plot_options, graph_id=gid) for gid, ag in
                  enumerate(self.analysis_groups)]

        else:
            key = lambda x: x.graph_id
            ans = sorted(self.analyses, key=key)
            gs = [self._panel_klass(analyses=list(ais),
                                    plot_options=self.plot_options,
                                    graph_id=gid)
                  for gid, ais in groupby(ans, key=key)]

            # if hasattr(self, 'references'):
            gg = groupby(self.references, key=key)
            for gi in gs:
                gid, ais = gg.next()
                gi.references = list(ais)

        for gi in gs:
            gi.make_figures()

        if self.titles:
            for ti, gi in zip(self.titles, gs):
                gi.title = ti
        elif self.plot_options.auto_generate_title:
            for i, gi in enumerate(gs):
                gi.title = self.plot_options.generate_title(gi.analyses, i)

        return gs

    def _get_npanels(self):
        return len(self.panels)

    def next_panel(self):
        return self.panel_gen.next()

        # ============= EOF =============================================
