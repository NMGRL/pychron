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
from typing import Any, List as TypingList

from traits.api import Any, HasTraits, List, Property

# from pychron.pipeline.plot.layout import FigureLayout
from pychron.core.helpers.iterfuncs import groupby_key


class FigureModel(HasTraits):
    panels = List
    npanels = Property(depends_on="panels[]")
    analyses = List
    references = List
    plot_options = Any
    # A class (callable) used to construct panels. This is intentionally not an
    # Instance trait; subclasses override it with a *class* (e.g. SeriesPanel).
    _panel_klass = Any
    titles = List

    def _panel_klass_default(self):
        # Lazy import to avoid import cycles.
        from pychron.pipeline.plot.panels.figure_panel import FigurePanel

        return FigurePanel

    # layout = Instance(FigureLayout, ())
    analysis_groups = List
    panel_gen = None
    force_refresh_panels = True
    _panel_signature = None

    def refresh(self, force: bool = False) -> bool:
        panels_rebuilt = False
        if force:
            panels_rebuilt = self.refresh_panels(force=True)
        elif self._panels_need_refresh():
            panels_rebuilt = self.refresh_panels()

        for p in self.panels:
            if not p.figures or force:
                p.make_graph()

            for f in p.figures:
                f.replot()

        return panels_rebuilt

    def dump_metadata(self) -> TypingList[Any]:
        ps = []

        for pp in self.panels:
            ps.append(pp.dump_metadata())

        return ps

    def load_metadata(self, metadata: TypingList[Any]) -> None:
        for pp, meta in zip(self.panels, metadata):
            pp.load_metadata(meta)

    # @on_trait_change('analyses[]')
    # def _analyses_items_changed(self):
    #     self.refresh_panels()

    def refresh_panels(self, force: bool = False) -> bool:
        if force or not self.panels or self.force_refresh_panels:
            ps = self._make_panels()
            self.panels = ps
            self._panel_signature = self._make_panel_signature()
            rebuilt = True
        else:
            self._sync_panels()
            rebuilt = False
        self.reset_panel_gen()
        return rebuilt

    def reset_panel_gen(self) -> None:
        self.panel_gen = (gi for gi in self.panels)

    def _panel_factory(self, *args, **kw):
        p = self._panel_klass(*args, **kw)
        return p

    def _make_panel_groups(self):
        if self.analysis_groups:
            gs = [
                self._panel_factory(
                    analyses=ag, plot_options=self.plot_options, graph_id=gid
                )
                for gid, ag in enumerate(self.analysis_groups)
            ]
        else:
            gs = [
                self._panel_factory(
                    analyses=list(ais), plot_options=self.plot_options, graph_id=gid
                )
                for gid, ais in groupby_key(self.analyses, "graph_id")
            ]
            # if hasattr(self, 'references'):
            gg = groupby_key(self.references, "graph_id")
            for gi in gs:
                try:
                    gid, ais = next(gg)
                    gi.references = list(ais)
                except StopIteration:
                    break

        return gs

    def _make_panels(self):
        gs = self._make_panel_groups()
        for gi in gs:
            gi.make_figures()

        if self.titles:
            for ti, gi in zip(self.titles, gs):
                gi.title = ti
        elif self.plot_options.auto_generate_title:
            for i, gi in enumerate(gs):
                gi.title = self.plot_options.generate_title(gi.analyses, i)

        return gs

    def _make_panel_signature(self):
        if self.analysis_groups:
            groups = self.analysis_groups
        else:
            groups = [list(ais) for _, ais in groupby_key(self.analyses, "graph_id")]

        titles = tuple(self.titles) if self.titles else ()
        return tuple(
            (
                index,
                tuple(sorted({getattr(ai, "group_id", 0) for ai in analyses})),
                len(analyses),
                titles[index] if index < len(titles) else None,
            )
            for index, analyses in enumerate(groups)
        )

    def _panels_need_refresh(self) -> bool:
        return self._panel_signature != self._make_panel_signature()

    def _sync_panels(self) -> None:
        groups = self._make_panel_groups()
        titles = tuple(self.titles) if self.titles else ()

        for index, (panel, new_panel) in enumerate(zip(self.panels, groups)):
            panel.analyses = new_panel.analyses
            panel.references = getattr(new_panel, "references", [])
            panel.plot_options = self.plot_options
            panel.graph_id = new_panel.graph_id
            if panel.figures:
                grouped = [list(ais) for _, ais in groupby_key(panel.analyses, "group_id")]
                for figure, analyses in zip(panel.figures, grouped):
                    figure.analyses = analyses
                    figure.options = self.plot_options
                    figure.graph_id = panel.graph_id
            if titles:
                if index < len(titles):
                    panel.title = titles[index]
            elif self.plot_options.auto_generate_title:
                panel.title = self.plot_options.generate_title(panel.analyses, index)

        self._panel_signature = self._make_panel_signature()

    def _get_npanels(self) -> int:
        return len(self.panels)

    def next_panel(self):
        return next(self.panel_gen)

        # ============= EOF =============================================
