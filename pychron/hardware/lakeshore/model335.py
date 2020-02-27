# ===============================================================================
# Copyright 2018 ross
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
from traitsui.api import Item, UItem, HGroup, VGroup, Spring

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.graph.plot_record import PlotRecord
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.hardware.lakeshore.base_controller import BaseLakeShoreController


class Model335TemperatureController(BaseLakeShoreController):
    graph_klass = StreamStackedGraph

    def _update_hook(self):
        r = PlotRecord((self.input_a, self.input_b), (0, 1), ('a', 'b'))
        return r

    def get_control_group(self):
        grp = VGroup(Spring(height=10, springy=False),
                     HGroup(Item('input_a', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                            Item('setpoint1'),
                            UItem('setpoint1_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)),
                     HGroup(Item('input_b', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                            Item('setpoint2'),
                            UItem('setpoint2_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)))
        return grp

    def graph_builder(self, g, **kw):
        g.plotcontainer.spacing = 10
        g.new_plot(xtitle='Time (s)', ytitle='InputA',
                   padding=[100, 10, 0, 60])
        g.new_series()

        g.new_plot(ytitle='InputB',
                   padding=[100, 10, 60, 0])
        g.new_series(plotid=1)
# ============= EOF =============================================
