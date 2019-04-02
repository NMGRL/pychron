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
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.nmgrl.furnace_manager import BaseFurnaceManager
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.hardware.labjack.ldeo_furnace import LamontFurnaceControl
from pychron.paths import paths


@provides(IFurnaceManager)
class LDEOFurnaceManager(BaseFurnaceManager):
    controller = Instance(LamontFurnaceControl)
    canvas = Instance(MapCanvas)
    dumper_canvas = Instance(DumperCanvas)

    settings_name = 'furnace_settings'

    def _controller_default(self):
        c = LamontFurnaceControl(name='controller',
                                 configuration_dir_name='furnace')
        return c

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
        self.info('Start update')
        self.reset_scan_timer(func=self._update_scan)

    def stop_update(self):
        self.info('Stop update')
        self._stop_update()

    def prepare_destroy(self):
        self.debug('prepare destroy')
        self._stop_update()
        # self.loader_logic.manager = None
        if self.timer:
            self.timer.stop()

    def get_process_value(self):
        pv = self.controller.get_process_value()
        return pv

    def extract(self, v, units='volts'):
        self.controller.extract(v, units, furnace=1)

    def move_to_position(self, pos, *args, **kw):
        self.debug('move to position {}'.format(pos))
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
                self.warning('Position is not either an integer or a list')
        self.debug('drop sample {}'.format(pos))
        self.controller.drop_ball(pos)

    def stop_motors(self):
        pass  # need to wire up enable line

    def get_active_pid_parameters(self):
        pass  # not implemented

    def set_pid_parameters(self, v):
        pass  # not implemented

    def set_setpoint(self, v):  # use 'extract' instead unless units are being parsed at a higher level
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
        self.debug('clear sample states')
        self._backup_sample_states()
        self._dump_sample_states(states=[])

    def _load_sample_states(self):
        self.debug('load sample states')
        p = paths.furnace_sample_states
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                states = yaml.load(rfile)
                self.debug('states={}'.format(states))
                for si in states:
                    hole = self.stage_manager.stage_map.get_hole(si)
                    self.debug('si={} hole={}'.format(si, hole))
                    if hole:
                        hole.analyzed = True

    def _dump_sample_states(self, states=None):
        if states is None:
            states = self.stage_manager.get_sample_states()

        self.debug('dump sample states')
        p = paths.furnace_sample_states
        with open(p, 'w') as wfile:
            yaml.dump(states, wfile)

    def _backup_sample_states(self):
        if os.path.isfile(paths.furnace_sample_states):
            root, base = os.path.split(paths.furnace_sample_states)
            bp = os.path.join(root, '~{}'.format(base))
            self.debug('backing up furnace sample states to {}'.format(bp))

            shutil.copyfile(paths.furnace_sample_states, bp)

    def _handle_state(self, new):
        if not isinstance(new, list):
            new = [new]

        for ni in new:
            self.dumper_canvas.update_switch_state(*ni)

    def _update_scan(self):
        d = self.controller.get_summary()
        if d:

            output1 = d.get('OP1')
            # output2 = d.get('OP2')  # not recorded right now
            temp1 = d.get('TC1')
            # temp2 = d.get('TC2')  # not recorded right now
            if temp1 is not None:
                self.temperature_readback = temp1
            if output1 is not None:
                if output1 < 0:
                    output1 = 0
                else:
                    output1 = round(output1, 2)
                self.output_percent_readback = output1 * 10  # this is a voltage on a 0-10 scale

            self._update_scan_graph(output1, temp1, 0)  # not writing setpoint at moment since not implemented

    def _stop_update(self):
        self.debug('stop update')
        self._alive = False
        self.timer.stop()

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
                temp_plot = self.graph.plots[0].plots['plot0'][0]
                setpoint_plot = self.graph.plots[0].plots['plot1'][0]

                temp_data = temp_plot.value.get_data()
                setpoint_data = setpoint_plot.value.get_data()

                ma = max(temp_data.max(), setpoint_data.max())
                if self.setpoint == 0:
                    mi = 0
                else:
                    mi = min(setpoint_data.min(), temp_data.min())

                self.graph.set_y_limits(min_=mi, max_=ma, pad='0.1', plotid=0)

            if self._recording:
                self.record_data_manager.write_to_frame((x, response or 0, output or 0))

    def _start_recording(self):
        self._recording = True
        self.record_data_manager = dm = self._record_data_manager_factory()
        dm.new_frame(directory=paths.furnace_scans_dir)
        dm.write_to_frame(('time', 'temperature', 'output'))
        self._start_time = time.time()

    def _stop_recording(self):
        self._recording = False

    def _graph_factory(self, *args, **kw):
        g = TimeSeriesStreamStackedGraph()
        # g.plotcontainer.padding_top = 5
        # g.plotcontainer.padding_right = 5
        g.new_plot(xtitle='Time (s)', ytitle='Temp. (C)', padding_top=5, padding_left=75, padding_right=5)
        g.set_scan_width(600, plotid=0)
        g.set_data_limits(1.8 * 600, plotid=0)

        # setpoint
        g.new_series(plotid=0, line_width=2,
                     render_style='connectedhold')
        # response
        g.new_series(plotid=0)

        g.new_plot(ytitle='Output (%)', padding_top=5, padding_left=75, padding_right=5)
        g.set_scan_width(600, plotid=1)
        g.set_data_limits(1.8 * 600, plotid=1)
        g.new_series(plotid=1)
        g.set_y_limits(min_=-2, max_=102, plotid=1)

        return g

# ============= EOF =============================================
