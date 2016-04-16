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

# ============= enthought library imports =======================
from traits.api import TraitError, Instance, Float, provides, Bool
# ============= standard library imports ========================
import os
import time
from threading import Thread
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.dumper_canvas import DumperCanvas
from pychron.canvas.canvas2D.video_canvas import VideoCanvas
from pychron.core.helpers.filetools import pathtolist
from pychron.core.ui.led_editor import LED
from pychron.extraction_line.switch_manager import SwitchManager
from pychron.furnace.furnace_controller import FurnaceController
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.loader_logic import LoaderLogic
from pychron.furnace.magnet_dumper import NMGRLMagnetDumper
from pychron.furnace.stage_manager import NMGRLFurnaceStageManager, BaseFurnaceStageManager
from pychron.graph.time_series_graph import TimeSeriesStreamGraph
from pychron.hardware.furnace.nmgrl.camera import NMGRLCamera
from pychron.hardware.linear_axis import LinearAxis
from pychron.managers.stream_graph_manager import StreamGraphManager
from pychron.paths import paths
from pychron.response_recorder import ResponseRecorder


class BaseFurnaceManager(StreamGraphManager):
    controller = Instance(FurnaceController)
    setpoint = Float(auto_set=False, enter_set=True)
    temperature_readback = Float
    stage_manager = Instance(BaseFurnaceStageManager)
    switch_manager = Instance(SwitchManager)
    response_recorder = Instance(ResponseRecorder)

    use_network = False

    def _controller_default(self):
        c = FurnaceController(name='controller',
                              configuration_dir_name='furnace')
        return c

    def _switch_manager_default(self):
        sm = SwitchManager(configuration_dir_name='furnace',
                           setup_name='furnace_valves')
        sm.on_trait_change(self._handle_state, 'refresh_state')
        return sm

    def _response_recorder_default(self):
        r = ResponseRecorder(response_device=self.controller,
                             output_device=self.controller)
        return r

    def _handle_state(self, new):
        pass


class Funnel(LinearAxis):
    pass


@provides(IFurnaceManager)
class NMGRLFurnaceManager(BaseFurnaceManager):
    funnel = Instance(Funnel)
    loader_logic = Instance(LoaderLogic)
    magnets = Instance(NMGRLMagnetDumper)
    temperature_readback_min = Float(0)
    temperature_readback_max = Float(1600.0)

    dumper_canvas = Instance(DumperCanvas)

    magnets_firing = Bool

    mode = 'normal'

    water_flow_led = Instance(LED, ())

    video_enabled = Bool
    video_canvas = Instance(VideoCanvas)
    camera = Instance(NMGRLCamera)

    funnel_down_enabled = Bool(True)
    funnel_up_enabled = Bool(False)
    settings_name = 'furnace_settings'

    _alive = False
    _guide_overlay = None
    _dumper_thread = None
    _magnets_thread = None
    _pid_str = None

    def activate(self):
        # pref_id = 'pychron.furnace'
        # bind_preference(self, 'update_period',
        # '{}.update_period'.format(pref_id))
        self.video_enabled = self.camera.get_image_data() is not None

        self.refresh_states()
        self.load_settings()
        self.reset_scan_timer(func=self._update_scan)

        self.stage_manager.refresh()

        # self._start_update()

    def test_furnace_cam(self):
        if self.camera:
            return self.camera.get_image_data() is not None

    def test_furnace_api(self):
        if self.controller:
            return self.controller.test_connection()

    def test_connection(self):
        self.debug('testing connection')
        return self.test_furnace_api()

    def refresh_states(self):
        self.switch_manager.load_indicator_states()

        self.funnel_down_enabled = True
        self.funnel_up_enabled = False
        if self.funnel_down():
            self.dumper_canvas.set_item_state('Funnel', True)
            self.funnel_down_enabled = False
            self.funnel_up_enabled = True

        self.dumper_canvas.invalidate_and_redraw()

    def prepare_destroy(self):
        self.debug('prepare destroy')
        self._stop_update()
        self.loader_logic.manager = None
        if self.timer:
            self.timer.stop()
            
    def get_response_blob(self):
        self.debug('get response blob')
        blob = self.response_recorder.get_response_blob()
        return blob

    def get_output_blob(self):
        self.debug('get output blob')
        blob = self.response_recorder.get_output_blob()
        return blob

    def get_achieved_output(self):
        self.debug('get achieved output')
        return self.response_recorder.max_response

    def set_response_recorder_period(self, p):
        self.debug('set response recorder period={}'.format(p))
        self.response_recorder.period = p

    def extract(self, v, **kw):
        self.debug('extract')
        # self.response_recorder.start()
        self.debug('set setpoint to {}'.format(v))
        self.setpoint = v

    def disable(self):
        self.debug('disable')
        # self.response_recorder.stop()
        self.setpoint = 0

    def start_response_recorder(self):
        self.response_recorder.start()

    def stop_response_recorder(self):
        self.response_recorder.stop()

    def move_to_position(self, pos, *args, **kw):
        self.debug('move to position {}'.format(pos))
        self.stage_manager.goto_position(pos)

    def dump_sample(self, block=False):
        self.debug('dump sample')
        if self._dumper_thread is None:
            if block:
                return self._dump_sample()
            else:
                self._dumper_thread = Thread(name='DumpSample', target=self._dump_sample)
                self._magnets_thread.setDaemon(True)
                self._dumper_thread.start()
        else:
            self.warning('dump already in progress')

    def fire_magnets(self):
        self.debug('fire magnets')
        if self._magnets_thread is None:
            self.magnets_firing = True
            self._magnets_thread = Thread(name='Magnets', target=self.actuate_magnets, kwargs={'check_logic': False})
            self._magnets_thread.setDaemon(True)
            self._magnets_thread.start()

    def start_jitter_feeder(self):
        self.debug('jitter feeder')
        self.stage_manager.start_jitter(turns=0.5, p1=0.1, p2=0.25)

    def stop_jitter_feeder(self):
        self.debug('stop jitter')
        self.stage_manager.stop_jitter()

    def configure_jitter_feeder(self):
        self.debug('configure jitter')
        self.stage_manager.feeder.configure()

    def is_dump_complete(self):
        ret = self._dumper_thread is None
        return ret

    def actuate_magnets(self, check_logic=True):
        self.debug('actuate magnets check_logic={}'.format(check_logic))
        check = True
        if check_logic:
            check = self.loader_logic.check('AM')

        if check:

            self.stage_manager.feeder.start_jitter()
            self.magnets.energize()

            time.sleep(0.05)
            while 1:
                if not self.magnets.is_energized():
                    break
                time.sleep(1)

            self.stage_manager.set_sample_dumped()
            self.magnets.denergize()
            time.sleep(5)

            self.stage_manager.feeder.stop_jitter()
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog('Actuating magnets not enabled\n\n{}'.format(cm))

        self._magnets_thread = None
        self.magnets_firing = False

    def lower_funnel(self):
        self.debug('lower funnel')
        if self.loader_logic.check('FD'):
            self.funnel_down_enabled = False
            self.funnel.lower()
            self.funnel_up_enabled = True
            self.dumper_canvas.set_item_state('Funnel', True)
            return True
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog('Lowering funnel not enabled\n\n{}'.format(cm))

    def raise_funnel(self):
        self.debug('raise funnel')
        if self.loader_logic.check('FU'):
            self.funnel_up_enabled = False
            self.funnel.raise_()
            self.funnel_down_enabled = True
            self.dumper_canvas.set_item_state('Funnel', False)
            return True
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog('Raising funnel not enabled\n\n{}'.format(cm))

    def get_active_pid_parameters(self):
        result = self._pid_str or ''
        self.debug('active pid ={}'.format(result))
        return result

    def set_pid_parameters(self, v):
        self.debug('setting pid parameters for {}'.format(v))
        from pychron.hardware.eurotherm.base import get_pid_parameters
        params = get_pid_parameters(v)
        if params:
            _, param_str = params
            self._pid_str = param_str
            self.controller.set_pid(param_str)

    def set_setpoint(self, v):
        self.debug('set setpoint={}'.format(v))
        self.set_pid_parameters(v)

        if self.controller:
            self.controller.set_setpoint(v)
            if not self._guide_overlay:
                self._guide_overlay = self.graph.add_horizontal_rule(v)

            self._guide_overlay.visible = bool(v)
            self._guide_overlay.value = v

            # ymi, yma = self.graph.get_y_limits()
            d = self.graph.get_data(axis=1)
            self.graph.set_y_limits(min_=0, max_=max(d.max(), v * 1.1))

            self.graph.redraw()

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

    # canvas
    def set_software_lock(self, name, lock):
        if self.switch_manager is not None:
            if lock:
                self.switch_manager.lock(name)
            else:
                self.switch_manager.unlock(name)

    def open_valve(self, name, **kw):
        if not self._open_logic(name):
            self.debug('logic failed')
            return False, False

        if self.switch_manager:
            return self.switch_manager.open_switch(name, **kw)

    def close_valve(self, name, **kw):
        if not self._close_logic(name):
            self.debug('logic failed')
            return False, False

        if self.switch_manager:
            return self.switch_manager.close_switch(name, **kw)

    def set_selected_explanation_item(self, item):
        pass

    # logic
    def get_switch_indicator_state(self, name):
        if self.switch_manager:
            return self.switch_manager.get_state_by_name(name, force=True)

    def get_flag_state(self, flag):
        self.debug('get_flag_state {}'.format(flag))

        if flag in ('no_motion', 'no_dump', 'funnel_up', 'funnel_down'):
            return getattr(self, flag)()
        return False

    def funnel_up(self):
        return self.funnel.in_up_position()

    def funnel_down(self):
        return self.funnel.in_down_position()

    def no_motion(self):
        v = not self.stage_manager.in_motion()
        self.debug('no motion {}'.format(v))
        return v

    def no_dump(self):
        v = not self.magnets.dump_in_progress()
        self.debug('no dump {}'.format(v))
        return v

    # private
    def _handle_state(self, new):
        self.dumper_canvas.update_switch_state(*new)

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
        if isinstance(state, bool):
            self.water_flow_led.state = 2 if state else 0
        else:
            self.water_flow_led.state = 1

        self._update_scan_graph()

    def _stop_update(self):
        self.debug('stop update')
        self._alive = False

    def _update_scan_graph(self):
        v = self.read_temperature(verbose=False)
        # v = random()
        # v = None
        if v is not None:
            x = self.graph.record(v, track_y=False)
            if self.graph_y_auto:
                mi, ma = self._get_graph_y_min_max()
                if self._guide_overlay:
                    gv = self._guide_overlay.value
                    mi, ma = min(gv, mi), max(gv, ma)

                self.graph.set_y_limits(min_=mi, max_=ma, pad='0.1')

            if self._recording:
                self.record_data_manager.write_to_frame((x, v))

    def _start_recording(self):
        self._recording = True
        self.record_data_manager = dm = self._record_data_manager_factory()
        dm.new_frame(directory=paths.furnace_scans_dir)
        dm.write_to_frame(('time', 'temperature'))
        self._start_time = time.time()

    def _stop_recording(self):
        self._recording = False

    def _graph_factory(self, *args, **kw):
        g = TimeSeriesStreamGraph()
        # g.plotcontainer.padding_top = 5
        # g.plotcontainer.padding_right = 5
        g.new_plot(xtitle='Time (s)', ytitle='Temp. (C)', padding_top=5, padding_right=5)
        g.set_scan_width(600)
        g.new_series()
        return g

    def _dump_sample(self):
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
        self.debug('dump sample started')
        for line in self._load_dump_script():
            self.debug(line)
            if not self._execute_script_line(line):
                self.debug('FAILED: {}'.format(line))
                ret = False
                break

        self._dumper_thread = None
        return ret

    def _load_dump_script(self):
        p = os.path.join(paths.device_dir, 'furnace', 'dump_sequence.txt')
        return pathtolist(p)

    def _execute_script_line(self, line):
        if ' ' in line:
            cmd, args = line.split(' ')
        else:
            cmd, args = line, None

        success = True
        if cmd == 'sleep':
            time.sleep(float(args))
        elif cmd == 'open':
            success, change = self.open_valve(args)
            if success:
                self.dumper_canvas.set_item_state(args, True)
        elif cmd == 'close':
            success, change = self.close_valve(args)
            if success:
                self.dumper_canvas.set_item_state(args, False)
        elif cmd == 'lower_funnel':
            if self.lower_funnel():
                self.dumper_canvas.set_item_state(args, True)
        elif cmd == 'raise_funnel':
            if self.raise_funnel():
                self.dumper_canvas.set_item_state(args, False)
        elif cmd == 'actuate_magnets':
            self.actuate_magnets()

        self.dumper_canvas.request_redraw()
        return success

    # handlers
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def _stage_manager_default(self):
        sm = NMGRLFurnaceStageManager(stage_manager_id='nmgrl.furnace.stage_map')
        return sm

    def _dumper_canvas_default(self):
        dc = DumperCanvas(manager=self)

        pathname = os.path.join(paths.canvas2D_dir, 'dumper.xml')
        configpath = os.path.join(paths.canvas2D_dir, 'dumper_config.xml')
        valvepath = os.path.join(paths.extraction_line_dir, 'valves.xml')
        dc.load_canvas_file(pathname, configpath, valvepath, dc)
        return dc

    def _camera_default(self):
        c = NMGRLCamera(name='camera', configuration_dir_name='furnace')
        return c

    def _video_canvas_default(self):
        vc = VideoCanvas(video=self.camera, show_axes=False, show_grids=False)
        vc.border_visible = False
        vc.padding = 5
        vc.fps = 10
        return vc

    def _funnel_default(self):
        f = Funnel(name='funnel', configuration_dir_name='furnace')
        return f

    def _loader_logic_default(self):
        l = LoaderLogic(manager=self)
        l.load_config()

        return l

    def _magnets_default(self):
        m = NMGRLMagnetDumper(name='magnets', configuration_dir_name='furnace')
        return m

# ============= EOF =============================================
