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
from pyface.timer.do_later import do_later
from traits.api import TraitError, Instance, Float, provides, Bool, Str, Property, Int

from pychron.canvas.canvas2D.dumper_canvas import DumperCanvas
from pychron.canvas.canvas2D.video_canvas import VideoCanvas
from pychron.core.helpers.filetools import pathtolist
from pychron.core.progress import open_progress
from pychron.core.yaml import yload
from pychron.experiment import ExtractionException
from pychron.furnace.base_furnace_manager import (
    BaseFurnaceManager,
    SwitchableFurnaceManager,
)
from pychron.furnace.configure_dump import ConfigureDump
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.nmgrl.furnace_controller import NMGRLFurnaceController
from pychron.furnace.nmgrl.loader_logic import LoaderLogic
from pychron.furnace.nmgrl.magnet_dumper import NMGRLRotaryDumper, BaseDumper
from pychron.furnace.nmgrl.stage_manager import NMGRLFurnaceStageManager
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.hardware.furnace.nmgrl.camera import NMGRLCamera
from pychron.hardware.linear_axis import LinearAxis
from pychron.paths import paths


class Funnel(LinearAxis):
    pass


@provides(IFurnaceManager)
class NMGRLFurnaceManager(SwitchableFurnaceManager):
    controller_klass = NMGRLFurnaceController
    funnel = Instance(Funnel)
    loader_logic = Instance(LoaderLogic)
    dumper = Instance(BaseDumper)

    temperature_readback_min = Float(0)
    temperature_readback_max = Float(1600.0)

    dumper_canvas = Instance(DumperCanvas)

    magnets_firing = Bool

    mode = "normal"

    # water_flow_led = Instance(LED, ())
    water_flow_state = Int

    video_enabled = Bool
    video_canvas = Instance(VideoCanvas)
    camera = Instance(NMGRLCamera)

    funnel_down_enabled = Bool(True)
    funnel_up_enabled = Bool(False)
    # settings_name = "furnace_settings"
    status_txt = Str

    dump_sample_enabled = Property(
        depends_on="dump_funnel_safety_override, funnel_up_enabled"
    )
    dump_funnel_safety_override = Bool

    _alive = False
    _dumper_thread = None
    _magnets_thread = None
    _pid_str = None
    _recorded_flow_state = None

    def activate(self):
        super().activate()

        self.video_enabled = bool(self.camera.get_image_data())

        self.refresh_states()
        self._load_sample_states()
        # self.load_settings()
        # self.start_update()

        self.stage_manager.refresh(warn=True)

        self.loader_logic.manager = self

    def test_furnace_cam(self):
        self.info("testing furnace cam")
        ret, err = False, ""
        if self.camera:
            ret = self.camera.get_image_data() is not None
        return ret, err

    #
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

        if self.funnel_down():
            self.dumper_canvas.set_item_state("Funnel", True)
            self.funnel_down_enabled = False
            self.funnel_up_enabled = True
        elif self.funnel_up():
            self.dumper_canvas.set_item_state("Funnel", False)
            self.funnel_down_enabled = True
            self.funnel_up_enabled = False
        else:
            self.funnel_up_enabled = True
            self.funnel_down_enabled = True

        self.dumper_canvas.invalidate_and_redraw()

    def prepare_destroy(self):
        super().prepare_destroy()
        self.loader_logic.manager = None

    def enable(self):
        self.debug("enable")
        if not self.controller.get_water_flow_state(verbose=False):
            raise ExtractionException()
        else:
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

    def fire_magnets(self):
        self.debug("fire magnets")
        if self._magnets_thread is None:
            self.magnets_firing = True
            self._magnets_thread = Thread(
                name="Magnets",
                target=self.actuate_magnets,
                kwargs={"check_logic": False},
            )
            self._magnets_thread.setDaemon(True)
            self._magnets_thread.start()

    def start_jitter_feeder(self):
        self.debug("jitter feeder")
        self.stage_manager.feeder.start_jitter(turns=0.5, p1=0.1, p2=0.25)

    def stop_jitter_feeder(self):
        self.debug("stop jitter")
        self.stage_manager.feeder.stop_jitter()

    def configure_jitter_feeder(self):
        self.debug("configure jitter")
        self.stage_manager.feeder.configure()

    def configure_dump(self):
        self.debug("configure dump")
        v = ConfigureDump(model=self)
        v.edit_traits()

    def is_dump_complete(self):
        ret = self._dumper_thread is None
        return ret

    def actuate_magnets(self, check_logic=True):
        self.debug("actuate magnets check_logic={}".format(check_logic))
        check = True
        if check_logic and not self.dump_funnel_safety_override:
            check = self.loader_logic.check("AM")

        if check:
            self.status_txt = "Actuating Magnets"

            self.stage_manager.feeder.start_jitter()
            self.dumper.energize()

            time.sleep(2)
            timeout = 60
            st = time.time()
            success = False
            self.debug("starting dump progress poll")
            while time.time() - st < timeout:
                if not self.dumper.dump_in_progress():
                    success = True
                    break
                time.sleep(3)

            if not success:
                self.debug("actuate magnets timeout, {}".format(timeout))

            self.stage_manager.set_sample_dumped()
            self._dump_sample_states()

            self.dumper.denergize()
            # time.sleep(5)

            self.stage_manager.feeder.stop_jitter()
            self.status_txt = ""
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog("Actuating magnets not enabled\n\n{}".format(cm))

        self._magnets_thread = None
        self.magnets_firing = False

    def lower_funnel(self):
        self.debug("lower funnel")
        if self.loader_logic.check("FD"):
            self.status_txt = "Lowering Funnel"
            self.funnel_down_enabled = False
            self.funnel.lower()
            self.funnel_up_enabled = True
            self.dumper_canvas.set_item_state("Funnel", True)
            self.status_txt = ""
            return True
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog("Lowering funnel not enabled\n\n{}".format(cm))

    def raise_funnel(self, force=False):
        self.debug("raise funnel. force={}".format(force))
        if self.loader_logic.check("FU") or force:
            self.status_txt = "Raising Funnel"
            self.funnel_up_enabled = False
            self.funnel.raise_()
            self.funnel_down_enabled = True
            self.dumper_canvas.set_item_state("Funnel", False)
            self.status_txt = ""
            return True
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog("Raising funnel not enabled\n\n{}".format(cm))

    # canvas
    def set_software_lock(self, name, lock):
        if self.switch_manager is not None:
            if lock:
                self.switch_manager.lock(name)
            else:
                self.switch_manager.unlock(name)

    def open_valve(self, name, **kw):
        if not self._open_logic(name):
            self.debug("logic failed")
            do_later(
                self.warning_dialog, "Open Valve Failed. Prevented by safety logic"
            )
            return False, False

        if self.switch_manager:
            return self.switch_manager.open_switch(name, **kw)

    def close_valve(self, name, **kw):
        if not self._close_logic(name):
            self.debug("logic failed")
            do_later(
                self.warning_dialog, "Close Valve Failed. Prevented by safety logic"
            )
            return False, False

        if self.switch_manager:
            return self.switch_manager.close_switch(name, **kw)

    def set_selected_explanation_item(self, item):
        pass

    # logic
    def get_switch_state(self, name):
        if self.switch_manager:
            return self.switch_manager.get_indicator_state(name)

    def get_flag_state(self, flag):
        self.debug("get_flag_state {}".format(flag))

        if flag in ("no_motion", "no_dump", "funnel_up", "funnel_down"):
            return getattr(self, flag)()
        return False

    def funnel_up(self):
        return self.funnel.in_up_position()

    def funnel_down(self):
        return self.funnel.in_down_position()

    def no_motion(self):
        v = not self.stage_manager.in_motion()
        self.debug("no motion {}".format(v))
        return v

    def no_dump(self):
        v = not self.dumper.dump_in_progress()
        self.debug("no dump {}".format(v))
        return v

    # private
    def _clear_sample_states(self):
        self.debug("clear sample states")
        self._backup_sample_states()
        self._dump_sample_states(states=[])

    def _load_sample_states(self):
        self.debug("load sample states")
        p = paths.furnace_sample_states
        if os.path.isfile(p):
            # with open(p, 'r') as rfile:
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

    def _open_logic(self, name):
        """
        check the logic rules to see if its ok to open "name"

        return True if ok
        """
        return self.loader_logic.open(name)

    def _close_logic(self, name):
        """
        check the logic rules to see if its ok to close "name"

        return True if ok

        """
        return self.loader_logic.close(name)

    def _update_scan(self):
        state = self.controller.get_water_flow_state(verbose=False)
        if state in (0, 1):
            # self.water_flow_led.state = 2 if state else 0
            self.water_flow_state = 2 if state else 0
        else:
            self.water_flow_state = 1

        write_water_state = (
            self._recorded_flow_state is None
            or self._recorded_flow_state != self.water_flow_state
        )

        if write_water_state:
            with open(os.path.join(paths.data_dir, "furnace_water.txt"), "a") as wfile:
                wfile.write("{},{}\n".format(time.time(), state))
                self._recorded_flow_state = self.water_flow_state

        super()._update_scan()

    def _update_scan_old(self):
        d = self.controller.get_summary(verbose=self.verbose_scan)
        if d:
            state = d.get("h2o_state")
            if state in (0, 1):
                # self.water_flow_led.state = 2 if state else 0
                self.water_flow_state = 2 if state else 0
            else:
                self.water_flow_state = 1

            write_water_state = (
                self._recorded_flow_state is None
                or self._recorded_flow_state != self.water_flow_state
            )

            if write_water_state:
                with open(
                    os.path.join(paths.data_dir, "furnace_water.txt"), "a"
                ) as wfile:
                    wfile.write("{},{}\n".format(time.time(), state))
                    self._recorded_flow_state = self.water_flow_state

            response = d.get("response")
            output = d.get("output")
            if response is not None:
                self.temperature_readback = response
            if output is not None:
                self.output_percent_readback = output

            self._set_scan_graph_values(response, output, d["setpoint"])

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
        1. open gate valve
        2. open shutters
        3. lower funnel
        4. actuate magnets
        5. raise funnel
        6. close shutters
        7. close gate valve
        :return:
        """

        ret = True
        self.debug("dump sample started")
        lines = self._load_dump_script()
        progress.max = len(lines)
        for i, line in enumerate(lines):
            self.debug(line)
            if not self._execute_script_line(line, progress):
                self.debug("FAILED: {}".format(line))
                ret = False
                break

        if not ret:
            self.warning_dialog("Sample dump failed at line {}: {}".format(i, line))
        else:
            self.information_dialog("Dump Successful")

        progress.close()
        self._dumper_thread = None
        return ret

    def _load_dump_script(self):
        p = os.path.join(paths.device_dir, "furnace", "dump_sequence.txt")
        return pathtolist(p)

    def _execute_script_line(self, line, progress):
        if " " in line:
            cmd, args = line.split(" ")
        else:
            cmd, args = line, None

        progress.change_message(
            "Dump Sequence: Command={}, Parameters={}".format(cmd, args)
        )
        time.sleep(0.5)

        success = True
        if cmd == "sleep":
            time.sleep(float(args))
        elif cmd == "open":
            success, change = self.open_valve(args)
            if success:
                self.dumper_canvas.set_item_state(args, True)
        elif cmd == "close":
            success, change = self.close_valve(args)
            if success:
                self.dumper_canvas.set_item_state(args, False)
        elif cmd == "lower_funnel":
            if self.lower_funnel():
                self.dumper_canvas.set_item_state(args, True)
        elif cmd == "raise_funnel":
            if self.raise_funnel():
                self.dumper_canvas.set_item_state(args, False)
        elif cmd == "actuate_magnets":
            self.actuate_magnets()

        self.dumper_canvas.request_redraw()
        return success

    def _get_dump_sample_enabled(self):
        return self.funnel_up_enabled or self.dump_funnel_safety_override

    # handlers
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def _stage_manager_default(self):
        sm = NMGRLFurnaceStageManager(stage_manager_id="nmgrl.furnace.stage_map")
        return sm

    def _dumper_canvas_default(self):
        dc = DumperCanvas(manager=self)

        pathname = os.path.join(paths.canvas2D_dir, "dumper.xml")
        configpath = os.path.join(paths.canvas2D_dir, "dumper_config.xml")
        valvepath = os.path.join(paths.extraction_line_dir, "valves.xml")
        dc.load_canvas_file(pathname, configpath, valvepath, dc)
        return dc

    def _camera_default(self):
        c = NMGRLCamera(name="camera", configuration_dir_name="furnace")
        return c

    def _video_canvas_default(self):
        vc = VideoCanvas(video=self.camera, show_axes=False, show_grids=False)
        vc.border_visible = False
        vc.padding = 5
        vc.fps = 10
        return vc

    def _funnel_default(self):
        f = Funnel(name="funnel", configuration_dir_name="furnace")
        return f

    def _loader_logic_default(self):
        l = LoaderLogic(manager=self)
        l.load_config()

        return l

    def _dumper_default(self):
        # m = NMGRLMagnetDumper(name='magnets', configuration_dir_name='furnace')
        m = NMGRLRotaryDumper(name="dumper", configuration_dir_name="furnace")
        return m


# ============= EOF =============================================
