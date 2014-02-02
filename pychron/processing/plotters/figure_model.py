#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, List, Property, Any, on_trait_change, Instance
#============= standard library imports ========================
from itertools import groupby
#============= local library imports  ==========================

class FigureModel(HasTraits):
    panels = List
    npanels = Property(depends_on='panels[]')
    analyses = List
    plot_options = Any
    _panel_klass = Instance('pychron.processing.plotters.figure_panel.FigurePanel')

    def refresh(self):
        for p in self.panels:
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

    @on_trait_change('analyses[]')
    def _analyses_items_changed(self):
        ps = self._make_panels()
        self.panels = ps
        self.panel_gen = (gi for gi in self.panels)

    def _make_panels(self):
        key = lambda x: x.graph_id
        ans = sorted(self.analyses, key=key)
        gs = [self._panel_klass(analyses=list(ais),
                                plot_options=self.plot_options,
                                graph_id=gid)
              for gid, ais in groupby(ans, key=key)]
        print gs
        return gs

    def _get_npanels(self):
        return len(self.panels)

    def next_panel(self):
        return self.panel_gen.next()

        #============= EOF =============================================
