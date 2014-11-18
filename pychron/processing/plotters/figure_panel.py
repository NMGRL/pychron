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
from math import isinf

from numpy import Inf, inf
from traits.api import HasTraits, Any, on_trait_change, List, Int, Str

#============= standard library imports ========================
from itertools import groupby

#============= local library imports  ==========================
from pychron.processing.analysis_graph import AnalysisStackedGraph


class FigurePanel(HasTraits):
    figures = List
    graph = Any
    analyses = Any
    plot_options = Any
    _index_attr = ''
    equi_stack = False
    graph_klass = AnalysisStackedGraph
    plot_spacing = Int
    meta = Any
    title = Str
    use_previous_limits=True

    @on_trait_change('analyses[]')
    def _analyses_items_changed(self):
        self.figures = self._make_figures()

    def _make_figures(self):
        key = lambda x: x.group_id
        ans = sorted(self.analyses, key=key)
        gs = [self._figure_klass(analyses=list(ais),
                                 group_id=gid)
              for gid, ais in groupby(ans, key=key)]
        return gs

    # def dump_metadata(self):
    #     return self.graph.dump_metadata()
    #
    # def load_metadata(self, md):
    #     self.graph.load_metadata(md)

    def make_graph(self):
        po = self.plot_options
        g = self.graph_klass(panel_height=200,
                             equi_stack=self.equi_stack,
                             container_dict=dict(padding=0,
                                                 spacing=self.plot_spacing or po.plot_spacing,
                                                 bgcolor=po.bgcolor))


        attr = po.index_attr
        center = None
        mi, ma = Inf, -Inf
        if attr:
            if po.use_static_limits:
                mi, ma = po.xlow, po.xhigh
            else:
                xmas, xmis = zip(*[(i.max_x(attr), i.min_x(attr))
                                   for i in self.figures])
                mi, ma = min(xmis), max(xmas)

                cs = [i.mean_x(attr) for i in self.figures]
                center = sum(cs) / len(cs)
                if po.use_centered_range:
                    w2 = po.centered_range / 2.0
                    mi, ma = center - w2, center + w2

        plots = list(po.get_aux_plots())
        if plots:
            for i, fig in enumerate(self.figures):
                fig.trait_set(xma=ma, xmi=mi,
                              center=center,
                              options=po,
                              graph=g,
                              title=self.title)

                if i == 0:
                    fig.build(plots)

                fig.suppress_ylimits_update = True
                fig.suppress_xlimits_update = True
                fig.plot(plots)
                fig.suppress_ylimits_update = False
                fig.suppress_xlimits_update = False
                ma, mi = max(fig.xma, ma), min(fig.xmi, mi)

            if self.use_previous_limits:
                # print plots[0], plots[0].has_xlimits(), plots[0].name
                if plots[0].has_xlimits():
                    tmi, tma = plots[0].xlimits
                    if tmi != -inf and tma != inf:
                        mi, ma = tmi, tma
                        print 'using previous limits', mi, ma

            if mi is None and ma is None:
                mi, ma = 0, 100

            if not (isinf(mi) or isinf(ma)):
                # print 'setting xlimits', mi, ma
                g.set_x_limits(mi, ma, pad=fig.xpad or 0)

            for fig in self.figures:
                for i in range(len(plots)):
                    fig.update_options_limits(i)

        self.graph = g
        return g.plotcontainer

        #============= EOF =============================================
