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
import time
from chaco.array_data_source import ArrayDataSource
from chaco.scales.time_scale import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from traits.api import Array
#============= standard library imports ========================
from numpy import array, Inf
#============= local library imports  ==========================
from pychron.processing.plotters.arar_figure import BaseArArFigure

N = 500


class Series(BaseArArFigure):
    xs = Array
    _omit_key = 'omit_series'

    def max_x(self, *args):
        if len(self.xs):
            return max(self.xs)
        return -Inf

    def min_x(self, *args):
        if len(self.xs):
            return min(self.xs)
        return Inf

    def mean_x(self, *args):
        if len(self.xs):
            return self.xs.mean()
        return 0

    def build(self, plots):
        graph = self.graph
        for po in plots:
            if po.use:
                p = graph.new_plot(padding=self.padding,
                                   ytitle=po.name,
                                   xtitle='Time')

                p.value_scale = po.scale
                p.padding_left = 75
                p.value_range.tight_bounds = False

    def plot(self, plots):
        """
            plot data on plots
        """

        omits=self._get_omitted(self.sorted_analyses, omit='omit_series')
        graph = self.graph

        xs = array([ai.timestamp for ai in self.sorted_analyses])
        #print plots, xs
        if plots:
            px = plots[0]

            if px.normalize == 'now':
                norm = time.time()
            else:
                norm = xs[-1]

            xs -= norm
            if not px.use_time_axis:
                xs /= 3600
            else:
                graph.convert_index_func = lambda x: '{:0.2f} hrs'.format(x / 3600.)

            self.xs = xs

            with graph.no_regression(refresh=True):
                plots = [po for po in plots if po.use]
                for i, po in enumerate(plots):
                    self._plot_series(po, i, omits)

                if plots:
                    graph.set_x_limits(min_=min(self.xs), max_=max(self.xs), pad='0.1',
                                       plotid=0)

    def _plot_series(self, po, pid, omits):
        graph = self.graph
        try:
            ys = [ai.nominal_value for ai in self._unpack_attr(po.name)]
            yerr = [ai.std_dev for ai in self._unpack_attr(po.name)]

            n = [ai.record_id for ai in self.sorted_analyses]

            args = graph.new_series(x=self.xs,
                                    y=ys,
                                    display_index=ArrayDataSource(data=n),
                                    yerror=yerr,
                                    fit=po.fit,
                                    plotid=pid,
                                    type='scatter',
                                    add_inspector=False,
                                    # add_tools=False
                                    )
            if len(args) == 2:
                scatter, p = args
            else:
                p, scatter, l = args

            sel=scatter.index.metadata.get('selections',[])
            sel+=omits
            scatter.index.metadata['selections']=list(set(sel))

            self._add_scatter_inspector(scatter)

            if po.use_time_axis:
                p.x_axis.tick_generator = ScalesTickGenerator(scale=CalendarScaleSystem())

            #p.value_scale = po.scale
            end_caps=True
            self._add_error_bars(scatter, yerr, 'y', 2, end_caps, visible=True)
        except (KeyError, ZeroDivisionError), e:
            print 'Series', e

    def _unpack_attr(self, attr):
        if attr.endswith('bs'):
            # f=lambda x: x.baseline.uvalue
            return (ai.get_baseline(attr).uvalue for ai in self.sorted_analyses)

        elif attr == 'PC':
            return super(Series, self)._unpack_attr(attr)
        else:
            return super(Series, self)._unpack_attr(attr)

            # f = lambda x: x.get_intensity()
            # return map(f, gs)

            #if attr.endswith('bs'):
            #    return (ai.isotopes[attr[:-2]].baseline.uvalue
            #            for ai in self.sorted_analyses)
            ##elif '/' in attr:
            ##    n, d = attr.split('/')
            #    #return (getattr(ai, n) / getattr(ai, d)
            #    #        for ai in self.sorted_analyses)
            #elif attr == 'PC':
            #    return (getattr(ai, 'peak_center')
            #            for ai in self.sorted_analyses)
            #else:
            #    return super(Series, self)._unpack_attr(attr)

    def update_graph_metadata(self, obj, name, old, new):
        sorted_ans = self.sorted_analyses
        if obj:
            hover = obj.metadata.get('hover')
            if hover:
                hoverid = hover[0]
                try:
                    self.selected_analysis = sorted_ans[hoverid]

                except IndexError, e:
                    print 'asaaaaa', e
                    return
            else:
                self.selected_analysis = None

            sel = self._filter_metadata_changes(obj, lambda x: x, sorted_ans)
            # self._set_renderer_selection()
            #self._set_selected(sorted_ans, sel)
            # set the temp_status for all the analyses
            #for i, a in enumerate(sorted_ans):
            #    a.temp_status = 1 if i in sel else 0
        # else:
            #sel = [i for i, a in enumerate(sorted_ans)
            #            if a.temp_status]
            # sel = self._get_omitted(sorted_ans, omit='omit_ideo')
            #print 'update graph meta'
            # self._rebuild_ideo(sel)
            # self.
#===============================================================================
# plotters
#===============================================================================

#===============================================================================
# overlays
#===============================================================================

#===============================================================================
# utils
#===============================================================================

#===============================================================================
# labels
#===============================================================================

#============= EOF =============================================
