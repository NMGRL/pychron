# ===============================================================================
# Copyright 2024 ross
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
from traits.api import Any
from traitsui.api import UItem, TableEditor, InstanceEditor, HGroup
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn

from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.hardware.bakeout_plc import BakeoutPLC
from pychron.loggable import Loggable
from pychron.managers.stream_graph_manager import StreamGraphManager


class BakeoutManager(StreamGraphManager):
    controller = Any
    settings_name = "bakeout_streaming"

    def _create_manager(
        self, klass, manager, params, port=None, host=None, remote=False
    ):
        return self.application.get_service(BakeoutManager)

    def _controller_default(self):
        return BakeoutPLC(name="controller", configuration_dir_name="bakeout")

    def prepare_destroy(self):
        self.set_streaming_active(False)
        self.stop_scan()
        self.controller.prepare_destroy()

    def activate(self):
        self.debug("asdfascasdcasdc")
        self.set_streaming_active(True)
        # self.bind_preferences()

        # self.load_event_marker_config()
        self.setup_scan()
        # self.readout_view.start()
        self.reset_scan_timer()

    def setup_scan(self):
        self._reset_graph()
        self.graph_scan_width = 10
        self._graph_scan_width_changed()

    def _update_scan_graph(self):
        for ci in self.get_display_channels():
            t = self.controller.read_temperature(ci.index)
            if t is None:
                continue

            sp = self.controller.read_setpoint(ci.index)
            dc = self.controller.read_duty_cycle(ci.index)
            self.controller.read_overtemp_ishighhigh(ci.index)

            self.graph.record(t, series=ci.index)
            self.graph.record(sp, series=ci.index + 1)
            self.graph.record(dc, plotid=1, series=ci.index)

    def _graph_factory(self, *args, **kw):
        g = TimeSeriesStreamStackedGraph()
        # g.plotcontainer.padding_top = 5
        # g.plotcontainer.padding_right = 5
        g.new_plot(
            xtitle="Time (s)",
            ytitle="Temp. (C)",
            padding_top=5,
            padding_left=75,
            padding_right=5,
            show_legend="ul",
        )
        g.set_scan_width(600, plotid=0)
        g.set_data_limits(1.8 * 600, plotid=0)

        # Output/Duty Cycle
        g.new_plot(
            ytitle="Output/Duty Cycle (%)",
            padding_top=5,
            padding_left=75,
            padding_right=5,
        )

        g.set_scan_width(600, plotid=1)
        g.set_data_limits(1.8 * 600, plotid=1)
        g.set_y_limits(min_=-2, max_=102, plotid=1)
        for channel in self.controller.channels:
            series, _ = g.new_series(
                plotid=0, color=channel.color, name=channel.shortname
            )
            g.new_series(
                plotid=0,
                # render_style="connectedhold",
                line_style="dash",
                color=series.color,
                name=f"{channel.shortname}, Setpoint",
            )

            g.new_series(plotid=1, name=channel.shortname, color=series.color)

        return g

    def get_display_channels(self):
        return [ci for ci in self.controller.channels if ci.display]


if __name__ == "__main__":
    b = BakeoutManager()
    b.activate()
    b.setup_scan()

# ============= EOF =============================================
