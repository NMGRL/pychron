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

from chaco.legend import Legend
from traits.api import HasTraits, Any, List, Int, Str
# ============= standard library imports ========================
from itertools import groupby
from numpy import inf
from math import isinf
import time
# ============= local library imports  ==========================
from pychron.processing.analysis_graph import AnalysisStackedGraph


class FigurePanel(HasTraits):
    figures = List
    # graph = Any
    analyses = Any
    plot_options = Any
    _index_attr = ''
    equi_stack = False

    _graph_klass = AnalysisStackedGraph
    _figure_klass = Any

    plot_spacing = Int(5)
    meta = Any
    title = Str
    use_previous_limits = True

    track_value = True

    # @on_trait_change('analyses[]')
    # def _analyses_items_changed(self):
    #     self.figures = self._make_figures()

    def make_figures(self):
        self.figures = self._make_figures()

    def _make_figures(self):
        key = lambda x: x.group_id
        ans = sorted(self.analyses, key=key)
        gs = [self._figure_klass(analyses=list(ais),
                                 group_id=gid)
              for gid, ais in groupby(ans, key=key)]
        return gs

    # def dump_metadata(self):
    # return self.graph.dump_metadata()
    #
    # def load_metadata(self, md):
    #     self.graph.load_metadata(md)

    def _get_init_xlimits(self):
        return None, inf, -inf

    def _make_graph_hook(self, g):
        pass

    # @caller
    def make_graph(self):

        st = time.time()
        po = self.plot_options

        # bgcolor = po.get_formatting_value('bgcolor')
        g = self._graph_klass(panel_height=200,
                              equi_stack=self.equi_stack,
                              container_dict=dict(padding=0,
                                                  spacing=self.plot_spacing or po.plot_spacing,
                                                  bgcolor=po.bgcolor))

        center, mi, ma = self._get_init_xlimits()

        plots = list(po.get_plotable_aux_plots())
        if plots:
            xpad = None

            if self.plot_options.include_legend:

                align = self.plot_options.legend_location
                a, b = align.split(' ')
                align = '{}{}'.format(a[0].lower(), b[0].lower())
                legend = Legend(align=align)
            else:
                legend = None

            ymas, ymis = [], []
            update_dict = {}
            for i, fig in enumerate(self.figures):
                fig.trait_set(xma=ma, xmi=mi,
                              ymas=ymas, ymis=ymis,
                              center=center,
                              options=po,
                              graph=g,
                              title=self.title,
                              **update_dict)

                if i == 0:
                    fig.build(plots)

                fig.suppress_ylimits_update = True
                fig.suppress_xlimits_update = True
                fig.plot(plots, legend)
                fig.suppress_ylimits_update = False
                fig.suppress_xlimits_update = False
                ma, mi = max(fig.xma, ma), min(fig.xmi, mi)
                ymas, ymis = fig.ymas, fig.ymis
                xpad = fig.xpad

                update_dict = fig.get_update_dict()

            if legend:
                g.plots[0].overlays.append(legend)

            if not self.track_value:
                for p in g.plots:
                    l, h = p.value_range.low, p.value_range.high
                    p.value_range.low_setting = l
                    p.value_range.high_setting = h

            if self.use_previous_limits:
                if plots[0].has_xlimits():
                    tmi, tma = plots[0].xlimits
                    if tmi != -inf and tma != inf:
                        mi, ma = tmi, tma
                        print 'using previous limits', mi, ma

            for i, p in enumerate(plots):
                if p.has_ylimits():
                    g.set_y_limits(p.ylimits[0], p.ylimits[1], plotid=i)
                elif p.calculated_ymin or p.calculated_ymax:
                    g.set_y_limits(p.calculated_ymin, p.calculated_ymax, plotid=i)
                elif p.ymin or p.ymax:
                    ymi, yma = p.ymin, p.ymax
                    if p.ymin > p.ymax:
                        yma = None

                    g.set_y_limits(ymi, yma, plotid=i)

            if mi is None and ma is None:
                mi, ma = 0, 100

            if not (isinf(mi) or isinf(ma)):
                # print 'setting xlimits', mi, ma, fig.xpad, self.plot_options.xpadding
                g.set_x_limits(mi, ma, pad=xpad or self.plot_options.xpadding)

            self.figures[0].post_make()
            for fig in self.figures:
                for i in range(len(plots)):
                    fig.update_options_limits(i)

        self._make_graph_hook(g)

        # print '----------------------- make graph {}'.format(time.time() - st)
        return g.plotcontainer

        # ============= EOF =============================================
