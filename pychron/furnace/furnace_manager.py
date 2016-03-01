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
from pyface.timer.do_later import do_after
from traits.api import TraitError, Instance, Float, provides, Int
# ============= standard library imports ========================
import os
import time
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.dumper_canvas import DumperCanvas
from pychron.core.helpers.filetools import pathtolist
from pychron.core.ui.thread import Thread
from pychron.extraction_line.switch_manager import SwitchManager
from pychron.furnace.funnel import NMGRLFunnel
from pychron.furnace.furnace_controller import FurnaceController
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.loader_logic import LoaderLogic
from pychron.furnace.magnet_dumper import NMGRLMagnetDumper
from pychron.furnace.stage_manager import NMGRLFurnaceStageManager, BaseFurnaceStageManager
from pychron.graph.stream_graph import StreamGraph
from pychron.managers.manager import Manager
from pychron.paths import paths
from pychron.response_recorder import ResponseRecorder


class BaseFurnaceManager(Manager):
    controller = Instance(FurnaceController)
    setpoint = Float(auto_set=False, enter_set=True)
    setpoint_readback = Float
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
        return sm

    def _response_recorder_default(self):
        r = ResponseRecorder(response_device=self.controller,
                             output_device=self.controller)
        return r


@provides(IFurnaceManager)
class NMGRLFurnaceManager(BaseFurnaceManager):
    funnel = Instance(NMGRLFunnel)
    loader_logic = Instance(LoaderLogic)
    magnets = Instance(NMGRLMagnetDumper)
    setpoint_readback_min = Float(0)
    setpoint_readback_max = Float(1600.0)

    graph = Instance(StreamGraph)
    update_period = Int(2)

    dumper_canvas = Instance(DumperCanvas)
    _alive = False
    _guide_overlay = None
    _dumper_thread = None
    _magnets_thread = None
    mode = 'normal'

    def activate(self):
        # pref_id = 'pychron.furnace'
        # bind_preference(self, 'update_period',
        # '{}.update_period'.format(pref_id))

        self._start_update()

    def prepare_destroy(self):
        self.debug('prepare destroy')
        self._stop_update()
        self.loader_logic.manager = None

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

    def extract(self, v):
        self.debug('extract')
        self.response_recorder.start()
        self.debug('set setpoint to {}'.format(v))
        self.setpoint = v

    def disable(self):
        self.debug('disable')
        self.response_recorder.stop()
        self.setpoint = 0
    def start_response_recorder(self):
        pass
    def stop_response_recorder(self):
        pass

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
            self._magnets_thread = Thread(name='Magnets', target=self.actuate_magnets)
            self._magnets_thread.setDaemon(True)
            self._magnets_thread.start()

    def is_dump_complete(self):
        ret = self._dumper_thread is None
        return ret

    def actuate_magnets(self):
        self.debug('actuate magnets')
        if self.loader_logic.check('AM'):
            self.magnets.energize()

            # jitter linear drive
            self.stage_manager.jitter()
            self.stage_manager.set_sample_dumped()

            self.magnets.denergize()
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog('Actuating magnets not enabled\n\n{}'.format(cm))

        self._magnets_thread = None

    def lower_funnel(self):
        self.debug('lower funnel')
        if self.loader_logic.check('FD'):
            # self.funnel.set_value(self.funnel.down_position)
            self.funnel.lower()
            # todo: update canvas state

            return True
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog('Lowering funnel not enabled\n\n{}'.format(cm))

    def raise_funnel(self):
        self.debug('raise funnel')
        if self.loader_logic.check('FU'):
            # self.funnel.set_value(self.funnel.up_position)
            self.funnel.raise_()
            # todo: update canvas state

            return True
        else:
            cm = self.loader_logic.get_check_message()
            self.warning_dialog('Raising funnel not enabled\n\n{}'.format(cm))

    def set_setpoint(self, v):
        self.debug('set setpoint={}'.format(v))
        if self.controller:
            # print self.controller, self.controller._cdevice
            self.controller.set_setpoint(v)
            if not self._guide_overlay:
                self._guide_overlay = self.graph.add_horizontal_rule(v)

            self._guide_overlay.visible = bool(v)
            self._guide_overlay.value = v

            # ymi, yma = self.graph.get_y_limits()
            d = self.graph.get_data(axis=1)
            self.graph.set_y_limits(min_=0, max_=max(d.max(), v * 1.1))

            self.graph.redraw()

    def read_setpoint(self, force=False):
        v = 0
        if self.controller:
            # force = update and not self.controller.is_scanning()
            v = self.controller.read_setpoint(force=force)

        try:
            self.setpoint_readback = v
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
    def get_switch_state(self, name):
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

    def _stop_update(self):
        self.debug('stop update')
        self._alive = False

    def _start_update(self):
        if not self.update_period:
            self.information_dialog('Please set an update period in Preferences/Furnace')
            return

        self.debug('starting update. period= {}s'.format(self.update_period))

        self._alive = True

        self.graph = g = StreamGraph()
        # g.plotcontainer.padding_top = 5
        # g.plotcontainer.padding_right = 5
        g.new_plot(xtitle='Time (s)', ytitle='Temp. (C)', padding_top=5, padding_right=5)
        g.set_scan_width(600)
        g.new_series()

        self._update_readback()

    def _update_readback(self):
        v = self.read_setpoint(force=True)
        scalar = 100
        if v is not None:
            self.graph.record(v, track_y=False)
            scalar = 1

        if self._alive:
            do_after(scalar * self.update_period * 1000, self._update_readback)

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

    def _funnel_default(self):
        f = NMGRLFunnel(name='funnel', configuration_dir_name='furnace')
        return f

    def _loader_logic_default(self):
        l = LoaderLogic(manager=self)
        l.load_config()

        return l

    def _magnets_default(self):
        m = NMGRLMagnetDumper(name='magnets', configuration_dir_name='furnace')
        return m


# ============= EOF =============================================
