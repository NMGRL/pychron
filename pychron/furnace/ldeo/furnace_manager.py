# ===============================================================================
# Copyright 2018 Stephen Cox
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

import yaml
from traits.api import Instance, provides

from pychron.canvas.canvas2D.dumper_canvas import DumperCanvas
from pychron.canvas.canvas2D.furnace_canvas import FurnaceCanvas
from pychron.canvas.canvas2D.map_canvas import MapCanvas
from pychron.core.yaml import yload
from pychron.furnace.base_furnace_manager import SwitchableFurnaceManager
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.nmgrl.furnace_manager import BaseFurnaceManager
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.hardware.labjack.ldeo_furnace import LamontFurnaceControl
from pychron.paths import paths


@provides(IFurnaceManager)
class LDEOFurnaceManager(SwitchableFurnaceManager):
    controller_klass = LamontFurnaceControl
    canvas = Instance(MapCanvas)
    dumper_canvas = Instance(DumperCanvas)

    # def _controller_default(self):
    #     c = LamontFurnaceControl(name="controller", configuration_dir_name="furnace")
    #     return c

    def _canvas_factory(self):
        c = FurnaceCanvas()
        return c

    def activate(self):
        # sn = self.controller.return_sn()
        # if 256 <= sn <= 2147483647:
        #     self.info('Labjack loaded')
        # else:
        #     self.warning('Invalid Labjack serial number: check Labjack connection')

        # self.refresh_states()
        self._load_sample_states()
        self.load_settings()
        self.start_update()

        # self.loader_logic.manager = self

    def start_update(self):
        self.info("Start update")
        self.reset_scan_timer(func=self._update_scan)

    def stop_update(self):
        self.info("Stop update")
        self._stop_update()

    def prepare_destroy(self):
        self.debug("prepare destroy")
        self._stop_update()
        # self.loader_logic.manager = None
        if self.timer:
            self.timer.stop()

    def extract(self, v, units="volts"):
        self.controller.extract(v, units, furnace=1)

    def move_to_position(self, pos, *args, **kw):
        self.debug("move to position {}".format(pos))
        if pos > 0:
            self.controller.goto_ball(pos)
        else:
            self.controller.returnfrom_ball(pos)

    def drop_sample(self, pos, *args, **kw):
        try:
            pos = int(pos)
        except TypeError:
            try:
                pos = int(pos[0])
            except TypeError:
                self.warning("Position is not either an integer or a list")
        self.debug("drop sample {}".format(pos))
        self.controller.drop_ball(pos)

    def stop_motors(self):
        pass  # need to wire up enable line

    # def get_active_pid_parameters(self):
    #     pass  # not implemented
    #
    # def set_pid_parameters(self, v):
    #     pass  # not implemented

    def set_setpoint(
        self, v
    ):  # use 'extract' instead unless units are being parsed at a higher level
        self.controller.set_furnace_setpoint(v, furnace=1)

    def read_output_percent(self, force=False, verbose=False):
        pv = self.get_process_value()
        return pv * 10

    def read_temperature(self, force=False, verbose=False):
        v = self.controller.readTC(1)
        return v

    # handlers
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

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

    def _handle_state(self, new):
        if not isinstance(new, list):
            new = [new]

        for ni in new:
            self.dumper_canvas.update_switch_state(*ni)

    def _update_scan(self):
        d = self.controller.get_summary()
        if d:
            output1 = d.get("OP1")
            # output2 = d.get('OP2')  # not recorded right now
            temp1 = d.get("TC1")
            # temp2 = d.get('TC2')  # not recorded right now
            if temp1 is not None:
                self.temperature_readback = temp1
            if output1 is not None:
                if output1 < 0:
                    output1 = 0
                else:
                    output1 = round(output1, 2)
                self.output_percent_readback = (
                    output1 * 10
                )  # this is a voltage on a 0-10 scale

            self._update_scan_graph(
                output1, temp1, 0
            )  # not writing setpoint at moment since not implemented


# ============= EOF =============================================
