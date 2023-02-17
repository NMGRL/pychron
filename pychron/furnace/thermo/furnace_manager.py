# ===============================================================================
# Copyright 2015 Jake Ross
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
import shutil
import time
from threading import Thread

import yaml
from traits.api import TraitError, Float, provides, Str

from pychron.core.progress import open_progress
from pychron.core.yaml import yload
from pychron.furnace.base_furnace_manager import BaseFurnaceManager, SwitchableFurnaceManager
from pychron.furnace.configure_dump import ConfigureDump
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.thermo.stage_manager import ThermoFurnaceStageManager
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.hardware.furnace.thermo.furnace_controller import ThermoFurnaceController
from pychron.paths import paths


@provides(IFurnaceManager)
class ThermoFurnaceManager(SwitchableFurnaceManager):
    controller_klass = ThermoFurnaceController

    temperature_readback_min = Float(0)
    temperature_readback_max = Float(1600.0)

    mode = "normal"


    status_txt = Str

    _alive = False
    _pid_str = None
    _dumper_thread = None

    def activate(self):
        self.refresh_states()
        self._load_sample_states()
        self.load_settings()
        self.start_update()

        self.stage_manager.refresh(warn=True)

    def start_update(self):
        self.info("Start update")
        self.reset_scan_timer(func=self._update_scan)

    def stop_update(self):
        self.info("Stop update")
        self._stop_update()

    # def test_furnace_api(self):
    #     self.info('testing furnace api')
    #     ret, err = False, ''
    #     if self.controller:
    #         ret = self.controller.test_connection()
    #     return ret, err
    #
    # def test_connection(self):
    #     self.info('testing connection')
    #     return self.test_furnace_api()

    def clear_sample_states(self):
        self._clear_sample_states()

    def refresh_states(self):
        self.switch_manager.load_indicator_states()

    def prepare_destroy(self):
        self.debug("prepare destroy")
        self._stop_update()
        if self.timer:
            self.timer.stop()

    def enable(self):
        self.debug("enable")
        return True

    def extract(self, v, **kw):
        self.debug("extract")
        # self.response_recorder.start()
        self.debug("set setpoint to {}".format(v))
        self.setpoint = v

    def disable(self):
        self.debug("disable")
        # self.response_recorder.stop()
        self.setpoint = 0

    disable_device = disable

    def move_to_position(self, pos, *args, **kw):
        self.debug("move to position {}".format(pos))
        self.stage_manager.goto_position(pos)

    def dump_sample(self, block=False):
        self.debug("dump sample")
        if self._dumper_thread is None:
            progress = open_progress(n=100)

            if block:
                return self._dump_sample(progress)
            else:
                self._dumper_thread = Thread(
                    name="DumpSample", target=self._dump_sample, args=(progress,)
                )
                self._dumper_thread.setDaemon(True)
                self._dumper_thread.start()
        else:
            self.warning_dialog("dump already in progress")

    def configure_dump(self):
        self.debug("configure dump")
        v = ConfigureDump(model=self)
        v.edit_traits()

    def is_dump_complete(self):
        ret = self._dumper_thread is None
        return ret


    # def set_pid_parameters(self, v):
    #     self.debug('setting pid parameters for {}'.format(v))
    #     from pychron.hardware.eurotherm.base import get_pid_parameters
    #     params = get_pid_parameters(v)
    #     if params:
    #         _, param_str = params
    #         self._pid_str = param_str
    #         self.controller.set_pid(param_str)


    # canvas
    def set_software_lock(self, name, lock):
        if self.switch_manager is not None:
            if lock:
                self.switch_manager.lock(name)
            else:
                self.switch_manager.unlock(name)

    # def open_valve(self, name, **kw):
    #     if not self._open_logic(name):
    #         self.debug('logic failed')
    #         do_later(self.warning_dialog, 'Open Valve Failed. Prevented by safety logic')
    #         return False, False
    #
    #     if self.switch_manager:
    #         return self.switch_manager.open_switch(name, **kw)
    #
    # def close_valve(self, name, **kw):
    #     if not self._close_logic(name):
    #         self.debug('logic failed')
    #         do_later(self.warning_dialog, 'Close Valve Failed. Prevented by safety logic')
    #         return False, False
    #
    #     if self.switch_manager:
    #         return self.switch_manager.close_switch(name, **kw)

    def set_selected_explanation_item(self, item):
        pass

    # logic
    # private
    def _clear_sample_states(self):
        self.debug("clear sample states")
        self._backup_sample_states()
        self._dump_sample_states(states=[])

    def _load_sample_states(self):
        self.debug("load sample states")
        p = paths.furnace_sample_states
        if os.path.isfile(p):
            states = yload(p)
            self.debug("states={}".format(states))
            for si in states:
                hole = self.stage_manager.stage_map.get_hole(si)
                self.debug("si={} hole={}".format(si, hole))
                if hole:
                    hole.analyzed = True

    def _dump_sample_states(self, states=None):
        if states is None:
            states = self.stage_manager.get_sample_states()

        self.debug("dump sample states")
        p = paths.furnace_sample_states
        with open(p, "w") as wfile:
            yaml.dump(states, wfile)

    def _backup_sample_states(self):
        if os.path.isfile(paths.furnace_sample_states):
            root, base = os.path.split(paths.furnace_sample_states)
            bp = os.path.join(root, "~{}".format(base))
            self.debug("backing up furnace sample states to {}".format(bp))

            shutil.copyfile(paths.furnace_sample_states, bp)

    # def _update_scan(self):
    #     response = self.controller.get_process_value(verbose=False)
    #     self.temperature_readback = response or 0
    #
    #     output = self.controller.get_output(verbose=False)
    #     self.output_percent_readback = output or 0
    #
    #     setpoint = self.controller.get_setpoint(verbose=False)
    #     self._update_scan_graph(response, output, setpoint or 0)

    # def _update_scan_graph(self, response, output, setpoint):
    #     x = None
    #     update = False
    #     if response is not None:
    #         x = self.graph.record(response, series=1, track_y=False)
    #         update = True
    #
    #     if output is not None:
    #         self.graph.record(output, x=x, series=0, plotid=1, track_y=False)
    #         update = True
    #
    #     if update:
    #         ss = self.graph.get_data(plotid=0, axis=1)
    #         if len(ss) > 1:
    #             xs = self.graph.get_data(plotid=0)
    #             xs[-1] = x
    #             self.graph.set_data(xs, plotid=0)
    #         else:
    #             self.graph.record(setpoint, x=x, track_y=False)
    #
    #         if self.graph_y_auto:
    #             temp_plot = self.graph.plots[0].plots["plot0"][0]
    #             setpoint_plot = self.graph.plots[0].plots["plot1"][0]
    #
    #             temp_data = temp_plot.value.get_data()
    #             setpoint_data = setpoint_plot.value.get_data()
    #
    #             ma = max(temp_data.max(), setpoint_data.max())
    #             if self.setpoint == 0:
    #                 mi = 0
    #             else:
    #                 mi = min(setpoint_data.min(), temp_data.min())
    #
    #             self.graph.set_y_limits(min_=mi, max_=ma, pad="0.1", plotid=0)
    #
    #         if self._recording:
    #             self.record_data_manager.write_to_frame((x, response or 0, output or 0))
    #
    # def _graph_factory(self, *args, **kw):
    #     g = TimeSeriesStreamStackedGraph()
    #     # g.plotcontainer.padding_top = 5
    #     # g.plotcontainer.padding_right = 5
    #     g.new_plot(
    #         xtitle="Time (s)",
    #         ytitle="Temp. (C)",
    #         padding_top=5,
    #         padding_left=75,
    #         padding_right=5,
    #     )
    #     g.set_scan_width(600, plotid=0)
    #     g.set_data_limits(1.8 * 600, plotid=0)
    #
    #     # setpoint
    #     g.new_series(plotid=0, line_width=2, render_style="connectedhold")
    #     # response
    #     g.new_series(plotid=0)
    #
    #     g.new_plot(ytitle="Output (%)", padding_top=5, padding_left=75, padding_right=5)
    #     g.set_scan_width(600, plotid=1)
    #     g.set_data_limits(1.8 * 600, plotid=1)
    #     g.new_series(plotid=1)
    #     g.set_y_limits(min_=-2, max_=102, plotid=1)
    #
    #     return g

    def _dump_sample(self, progress):
        """

        :return:
        """

        ret = True
        self.debug("dump sample started")

    # handlers
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def _stage_manager_default(self):
        sm = ThermoFurnaceStageManager(stage_manager_id="thermo.furnace.stage_map")
        return sm


# ============= EOF =============================================
