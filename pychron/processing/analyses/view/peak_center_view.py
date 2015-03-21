# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from chaco.tools.cursor_tool import CursorTool
from traits.api import HasTraits, Instance
from traitsui.api import View, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.graph.tools.cursor_tool_overlay import CursorToolOverlay


class PeakCenterView(HasTraits):
    graph = Instance(Graph, ())
    name = 'PeakCenter'

    def load(self, an):
        if an.peak_center_data:
            g = self.graph
            g.new_plot(xtitle='DAC', ytitle='Intensity')
            xs, ys = an.peak_center_data

            s, p = g.new_series(xs, ys)
            s.index.sort_order = 'ascending'

            t = CursorTool(s,
                           drag_button="left",
                           marker_size=5,
                           color='darkgreen')

            s.overlays.append(t)
            dto = CursorToolOverlay(
                component=p,
                tool=t)
            p.overlays.append(dto)
            t.current_position = an.peak_center, 0

            g.add_vertical_rule(an.peak_center)
            g.add_plot_label('Center={:0.5f} V'.format(an.peak_center),
                             font='modern 12',
                             color='darkgreen')
            g.set_y_limits(pad='0.05', plotid=0)

            return True

    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v


# ============= EOF =============================================

