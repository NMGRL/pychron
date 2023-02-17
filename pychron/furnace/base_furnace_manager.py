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
import os
import time

from traits.api import Instance, Float, Bool, Any
from traits.trait_errors import TraitError

from pychron.extraction_line.switch_manager import SwitchManager
from pychron.furnace.base_stage_manager import BaseFurnaceStageManager
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.managers.stream_graph_manager import StreamGraphManager
from pychron.paths import paths
from pychron.response_recorder import ResponseRecorder


class BaseFurnaceManager(StreamGraphManager):
    controller_klass = None
    controller = Any
    settings_name = "furnace_settings"

    setpoint = Float(auto_set=False, enter_set=True)
    temperature_readback = Float
    output_percent_readback = Float

    response_recorder = Instance(ResponseRecorder)

    use_network = False
    verbose_scan = Bool(False)

    _pid_str = None

    def activate(self):
        self.debug('activate')
        self.load_settings()
        self.start_update()

    def prepare_destroy(self):
        self.debug("prepare destroy")
        self._stop_update()

    def start_update(self):
        self.info("Start update")
        self.reset_scan_timer(func=self._update_scan)

    def stop_update(self):
        self.info("Stop update")
        self._stop_update()

    def check_heating(self):
        pass

    def _controller_default(self):
        if self.controller_klass is None:
            raise NotImplementedError
        c = self.controller_klass(name="controller", configuration_dir_name="furnace")
        return c

    def _response_recorder_default(self):
        r = ResponseRecorder(
            response_device=self.controller, output_device=self.controller
        )
        return r

    def _handle_state(self, new):
        pass

    def test_furnace_api(self):
        self.info("testing furnace api")
        ret, err = False, ""
        if self.controller:
            ret, err = self.controller.test_connection()
        return ret, err

    def test_connection(self):
        self.info("testing connection")
        return self.test_furnace_api()

    def get_process_value(self):
        return self.controller.get_process_value()

    def check_reached_setpoint(self, v, n, tol, std):
        return self.response_recorder.check_reached_setpoint(v, n, tol, std)

    def start_response_recorder(self):
        self.response_recorder.start()

    def stop_response_recorder(self):
        self.response_recorder.stop()

    def get_setpoint_blob(self):
        self.debug("get setpoint blob")
        blob = self.response_recorder.get_setpoint_blob()
        return blob

    def get_response_blob(self):
        self.debug("get response blob")
        blob = self.response_recorder.get_response_blob()
        return blob

    def get_output_blob(self):
        self.debug("get output blob")
        blob = self.response_recorder.get_output_blob()
        return blob

    def get_achieved_output(self):
        self.debug("get achieved output")
        return self.response_recorder.max_response

    def set_response_recorder_period(self, p):
        self.debug("set response recorder period={}".format(p))
        self.response_recorder.period = p


    def get_active_pid_parameters(self):
        result = self._pid_str or ""
        self.debug("active pid ={}".format(result))
        return result

    def set_pid_parameters(self, v):
        self.debug("setting pid parameters for {}".format(v))
        from pychron.hardware.eurotherm.base import (
            get_pid_parameters,
            modify_pid_parameter,
        )

        params = get_pid_parameters(v)
        if params:
            _, param_str = params
            if self.use_full_power:
                param_str = modify_pid_parameter(param_str, "HO", 100)
            self._pid_str = param_str
            self.controller.set_pid(param_str)

    def set_setpoint(self, v):
        self.debug("set setpoint={}".format(v))
        self.set_pid_parameters(v)

        if self.controller:
            self.controller.set_setpoint(v)

            self.graph.record(v)
            d = self.graph.get_data(axis=1)

            if not self.graph_y_auto:
                self.graph.set_y_limits(
                    min_=min(d.min(), v) * 0.9, max_=max(d.max(), v) * 1.1
                )

            self.graph.redraw()

    def read_output_percent(self, force=False, verbose=False):
        v = 0
        if self.controller:
            # force = update and not self.controller.is_scanning()
            v = self.controller.read_output_percent(force=force, verbose=verbose)

        try:
            self.output_percent_readback = v
            return v
        except TraitError:
            pass

    def read_temperature(self, force=False, verbose=False):
        v = 0
        if self.controller:
            # force = update and not self.controller.is_scanning()
            v = self.controller.read_temperature(force=force, verbose=verbose)

        try:
            self.temperature_readback = v
            return v
        except TraitError:
            pass

    # private
    def _stop_update(self):
        self.debug("stop update")
        self._alive = False
        if self.timer:
            self.timer.stop()

    def _start_recording(self):
        self._recording = True
        self.record_data_manager = dm = self._record_data_manager_factory()
        dm.new_frame(directory=paths.furnace_scans_dir)
        dm.write_to_frame(("time", "temperature", "output"))
        self._start_time = time.time()

    def _stop_recording(self):
        self._recording = False
    def _update_scan(self):
        response = self.controller.get_process_value(verbose=False)
        self.temperature_readback = response or 0

        output = self.controller.get_output(verbose=False)
        self.output_percent_readback = output or 0

        setpoint = self.controller.get_setpoint(verbose=False)
        self._update_scan_graph(response, output, setpoint or 0)

    def _update_scan_graph(self, response, output, setpoint):
        x = None
        update = False
        if response is not None:
            x = self.graph.record(response, series=1, track_y=False)
            update = True

        if output is not None:
            self.graph.record(output, x=x, series=0, plotid=1, track_y=False)
            update = True

        if update:
            ss = self.graph.get_data(plotid=0, axis=1)
            if len(ss) > 1:
                xs = self.graph.get_data(plotid=0)
                xs[-1] = x
                self.graph.set_data(xs, plotid=0)
            else:
                self.graph.record(setpoint, x=x, track_y=False)

            if self.graph_y_auto:
                temp_plot = self.graph.plots[0].plots["plot0"][0]
                setpoint_plot = self.graph.plots[0].plots["plot1"][0]

                temp_data = temp_plot.value.get_data()
                setpoint_data = setpoint_plot.value.get_data()

                ma = max(temp_data.max(), setpoint_data.max())
                if self.setpoint == 0:
                    mi = 0
                else:
                    mi = min(setpoint_data.min(), temp_data.min())

                self.graph.set_y_limits(min_=mi, max_=ma, pad="0.1", plotid=0)

            if self._recording:
                self.record_data_manager.write_to_frame((x, response or 0, output or 0))

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
        )
        g.set_scan_width(600, plotid=0)
        g.set_data_limits(1.8 * 600, plotid=0)

        # setpoint
        g.new_series(plotid=0, line_width=2, render_style="connectedhold")
        # response
        g.new_series(plotid=0)

        g.new_plot(ytitle="Output (%)", padding_top=5, padding_left=75, padding_right=5)
        g.set_scan_width(600, plotid=1)
        g.set_data_limits(1.8 * 600, plotid=1)
        g.new_series(plotid=1)
        g.set_y_limits(min_=-2, max_=102, plotid=1)

        return g

class SwitchableFurnaceManager(BaseFurnaceManager):
    stage_manager = Instance(BaseFurnaceStageManager)
    switch_manager = Instance(SwitchManager)
    def _switch_manager_default(self):
        sm = SwitchManager(configuration_dir_name="furnace")

        sm.valves_path = os.path.join(paths.extraction_line_dir, "furnace_valves.xml")
        sm.on_trait_change(self._handle_state, "refresh_state")
        return sm
# ============= EOF =============================================
