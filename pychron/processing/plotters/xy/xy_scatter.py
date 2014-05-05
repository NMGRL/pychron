#===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Instance

#============= standard library imports ========================
from numpy import array
#============= local library imports  ==========================
from uncertainties import nominal_value
from pychron.processing.plotters.xy.xy_scatter_tool import XYScatterTool
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
from pychron.pychron_constants import NULL_STR


class XYScatterEditor(GraphEditor):
    update_graph_on_set_items = True
    tool = Instance(XYScatterTool, ())

    def rebuild(self):
        self.rebuild_graph()

    def load_fits(self, refiso):
        pass

    def load_tool(self, tool=None):
        pass

    def dump_tool(self):
        pass

    def _normalize(self, vs, scalar):
        vs = array(sorted(vs))
        vs -= vs[0]
        return vs / scalar

    def _pretty(self, v):
        return ' '.join(map(str.capitalize, v.split('_')))

    def _rebuild_graph(self):
        ans = self.analyses
        if ans:
            g = self.graph
            g.new_plot()

            tool = self.tool

            i_attr = tool.index_attr
            v_attr = tool.value_attr

            xs = [nominal_value(ai.get_value(i_attr)) for ai in ans]
            ys = [nominal_value(ai.get_value(v_attr)) for ai in ans]

            if i_attr == 'timestamp':
                xtitle = 'Normalized Analysis Time'
                xs = self._normalize(xs, self.tool.index_time_scalar)
            else:
                xtitle = i_attr

            if v_attr == 'timestamp':
                ytitle = 'Normalized Analysis Time'
                ys = self._normalize(ys, self.tool.value_time_scalar)
            else:
                ytitle = v_attr

            ytitle = self._pretty(ytitle)
            xtitle = self._pretty(xtitle)

            kw = tool.get_marker_dict()
            fit = tool.fit
            fit = fit if fit != NULL_STR else False
            mn, mx = min(xs), max(xs)
            g.set_x_limits(mn, mx, pad='0.1')

            mn, mx = min(ys), max(ys)
            g.set_y_limits(mn, mx, pad='0.1')

            g.new_series(x=xs, y=ys, fit=fit, type='scatter', **kw)
            g.set_x_title(xtitle)
            g.set_y_title(ytitle)

#============= EOF =============================================

