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
#============= local library imports  ==========================
from pychron.processing.plotters.xy.xy_scatter_tool import XYScatterTool
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor


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

    def _rebuild_graph(self):
        ans = self.analyses
        if ans:
            g = self.graph
            p = g.new_plot()
            p.index_range.tight_bounds = False
            p.value_range.tight_bounds = False

            tool = self.tool

            i_attr = tool.index_attr
            v_attr = tool.value_attr
            xs = [ai.get_isotope(i_attr).value for ai in ans]
            ys = [ai.get_isotope(v_attr).value for ai in ans]

            kw = dict(marker=tool.marker, marker_size=tool.marker_size)
            g.new_series(x=xs, y=ys, fit=False, type='scatter', **kw)

            g.set_x_title(i_attr)
            g.set_y_title(v_attr)

#============= EOF =============================================

