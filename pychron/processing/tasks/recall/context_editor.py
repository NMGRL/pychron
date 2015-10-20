# ===============================================================================
# Copyright 2014 Jake Ross
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
from chaco.scales.time_scale import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from chaco.ticks import AbstractTickGenerator
from numpy import arange
from traits.api import List, Instance, Int, Any, Property
from traitsui.api import View, UItem, TabularEditor, VGroup, HGroup, VSplit, spring
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import CheckListEditor
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value
from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.pychron_constants import ARGON_KEYS


class StaticTickGenerator(AbstractTickGenerator):
    _ticks = None

    def get_ticks(self, *args, **kw):
        return self._ticks


class ContextGraph(StackedGraph):
    def new_plot(self, **kw):
        p = super(ContextGraph, self).new_plot(**kw)
        p.x_axis.tick_generator = ScalesTickGenerator(scale=CalendarScaleSystem())
        return p


class ContextAdapter(TabularAdapter):
    columns = [('Run ID', 'record_id'),
               ('Time', 'rundate'),
               ('Sample', 'sample'),
               ('Cleanup', 'cleanup'),
               ('Duration', 'duration'),
               ('Extract', 'extract_value'),
               ('Position', 'position'),
               ('Tag', 'tag'),
               ('Ar40', 'ar40'),
               ('Ar39', 'ar39'),
               ('Ar38', 'ar38'),
               ('Ar37', 'ar37'),
               ('Ar36', 'ar36')]
    font = '10'
    record_id_width = Int(90)
    rundate_width = Int(125)
    sample_width = Int(100)
    cleanup_width = Int(80)
    duration_width = Int(80)
    extract_value_width = Int(80)
    position_width = Int(80)
    tag_width = Int(50)

    ar40_width = Int(70)
    ar39_width = Int(70)
    ar38_width = Int(70)
    ar37_width = Int(70)
    ar36_width = Int(70)

    ar40_text = Property
    ar39_text = Property
    ar38_text = Property
    ar37_text = Property
    ar36_text = Property

    def _get_ar40_text(self):
        return self._get_intensity('Ar40')

    def _get_ar39_text(self):
        return self._get_intensity('Ar39')

    def _get_ar38_text(self):
        return self._get_intensity('Ar38')

    def _get_ar37_text(self):
        return self._get_intensity('Ar37')

    def _get_ar36_text(self):
        return self._get_intensity('Ar36')

    def _get_intensity(self, k):
        return floatfmt(nominal_value(self.item.get_value(k)))

    def get_bg_color(self, obj, trait, row, column=0):
        color = 'white'
        if self.item == obj.root_analysis:
            color = 'green'
        return color


class ContextEditor(BaseTraitsEditor):
    basename = 'context'

    graph = Instance(ContextGraph)
    analyses = List
    selected = List
    attributes = List(['cleanup', 'duration', 'extract_value'])
    available_attributes = List(['cleanup', 'duration', 'extract_value',
                                 'position', 'peak_center', 'tag'] + list(ARGON_KEYS))
    root_analysis = Any

    def _graph_default(self):
        g = ContextGraph()
        return g

    def _selected_changed(self):
        self._replot()

    def _attributes_changed(self):
        self._replot()

    def _get_data(self, ans, ai, xs):
        if ai == 'position':
            def ysfunc(aa):
                for ai in aa:
                    pos = ai.position
                    t = ai.timestamp
                    try:
                        yield ai, t, int(pos)
                    except ValueError:
                        if '.' in pos:
                            continue
                        else:
                            for p in pos.split(','):
                                try:
                                    yield ai, t, int(p)
                                except ValueError:
                                    pass

            xy = list(ysfunc(ans))
            if xy:
                ans, xs, ys = map(list, zip(*xy))
            else:
                ans, xs, ys = [], [], []

            rs = list(ysfunc([self.root_analysis]))
            rxs = [ri[1] for ri in rs]
            rs = [ri[2] for ri in rs]
        else:
            rxs = [self.root_analysis.timestamp]
            if ai == 'tag':
                tags = list({getattr(a, ai) for a in ans})
                self._tags = tags

                def func(x):
                    return tags.index(x.tag) + 1
            elif ai in ARGON_KEYS:
                def func(x):
                    return nominal_value(x.get_value(ai))
            else:
                func = lambda x: getattr(x, ai)
                # ys=[getattr(a, ai) for a in ans]
                # rs=[getattr(self.root_analysis, ai)]

            ys = [func(a) for a in ans]
            rs = [func(self.root_analysis)]

        return ans, xs, ys, rxs, rs

    def _replot(self):
        g = self.graph
        g.clear()
        ans = self.selected
        if ans and self.attributes:
            # to=ans[0].timestamp
            to = 0
            ts = [a.timestamp - to for a in ans]
            for i, ai in enumerate(reversed(self.attributes)):
                aa, xs, ys, rxs, rs = self._get_data(ans, ai, ts)

                p = g.new_plot()
                p.y_axis.title = ai

                if ai == 'tag':
                    p.y_axis.tick_label_formatter = lambda x: '{}'.format(self._tags[int(x - 1)])
                    p.y_axis.tick_generator = StaticTickGenerator(_ticks=arange(len(self._tags)))

                s, _ = g.new_series(xs, ys,
                                    marker='circle',
                                    marker_size=3,
                                    type='scatter')

                self._add_inspector(s, analyses=aa)
                s, _ = g.new_series(rxs, rs,
                                    marker='circle',
                                    marker_size=3,
                                    type='scatter',
                                    color='red')

                self._add_inspector(s, analyses=[self.root_analysis])
                if ai == 'tag':
                    g.set_y_limits(0, len(self._tags) + 1, plotid=i)
                else:
                    g.set_y_limits(pad='0.1', plotid=i)

            g.set_x_limits(pad='0.1')
            g.set_x_title('Time', plotid=0)

    def _add_inspector(self, scatter, analyses=None):
        if analyses is None:
            analyses = self.analyses
        value_format = lambda x: '{:0.5f}'.format(x)
        point_inspector = AnalysisPointInspector(scatter,
                                                 analyses=analyses,
                                                 convert_index=lambda x: '{:0.3f}'.format(x),
                                                 value_format=value_format)
        # additional_info=additional_info)

        pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                   tool=point_inspector)

        scatter.overlays.append(pinspector_overlay)
        scatter.tools.append(point_inspector)

    def traits_view(self):
        v = View(VSplit(UItem('analyses', editor=TabularEditor(adapter=ContextAdapter(),
                                                               multi_select=True,
                                                               selected='selected')),
                        HGroup(VGroup(UItem('attributes',
                                            style='custom',
                                            editor=CheckListEditor(name='available_attributes',
                                                                   cols=1)), spring),
                               UItem('graph', style='custom'))))
        return v

# ============= EOF =============================================



