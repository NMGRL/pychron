# ===============================================================================
# Copyright 2016 Jake Ross
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

import json
import time
# ============= enthought library imports =======================
# ============= standard library imports ========================
import json
import os
from threading import Thread, Event
import time

import yaml

# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_bool
from pychron.furnace.firmware import PARAMETER_REGISTRY, __version__
from pychron.hardware.arduino.rotary_dumper import RotaryDumper
from pychron.hardware.dht11 import DHT11
from pychron.hardware.eurotherm.headless import HeadlessEurotherm
from pychron.hardware.gauges.granville_phillips.headless_micro_ion_controller import HeadlessMicroIonController
from pychron.hardware.labjack.headless_u3_lv import HeadlessU3LV
from pychron.hardware.mdrive.headless import HeadlessMDrive
from pychron.hardware.watlow.headless_ezzone import HeadlessWatlowEZZone
from pychron.headless_loggable import HeadlessLoggable
from pychron.image.rpi_camera import RPiCamera
from pychron.messaging.broadcaster import Broadcaster
from pychron.paths import paths

DEVICES = {'controller': HeadlessEurotherm,
           'switch_controller': HeadlessU3LV,
           'funnel': HeadlessMDrive,
           'feeder': HeadlessMDrive,
           'temp_hum': DHT11,
           'camera': RPiCamera,
           'first_stage_gauge': HeadlessMicroIonController,
           'backside_furnace_gauge': HeadlessMicroIonController,
           'bakeout1': HeadlessWatlowEZZone,
           'bakeout2': HeadlessWatlowEZZone,
           'rotary_dumper': RotaryDumper}


def debug(func):
    def wrapper(obj, data):
        #       obj.debug('------ {}, data={}'.format(func.__name__, data))
        r = func(obj, data)
        #        obj.debug('------ result={}'.format(r))
        return r

    return wrapper


class FirmwareManager(HeadlessLoggable):
    controller = None
    switch_controller = None
    funnel = None
    feeder = None
    temp_hum = None
    camera = None
    rotary_dumper = None

    _switch_mapping = None
    _switch_indicator_mapping = None
    _is_energized = False

    _use_video_service = False
    _use_broadcast_service = False
    _broadcast_port = 9000
    _start_time = 0
    _broadcaster = None
    _broadcast_stop_event = None

    def bootstrap(self):
        self._start_time = time.time()
        p = paths.furnace_firmware
        if p and os.path.isfile(p):
            with open(p, 'r') as rfile:
                yd = yaml.load(rfile)

            self._load_config(yd['config'])
            self._load_devices(yd['devices'])
            self._load_switch_mapping(yd['switch_mapping'])
            self._load_switch_indicator_mapping(yd['switch_indicator_mapping'])
            self._load_funnel(yd['funnel'])
            self._load_magnets(yd['magnets'])
            self._load_rotary_dumper()

            if self._use_broadcast_service:
                self._broadcaster = Broadcaster()
                self._broadcaster.setup(self._broadcaster_port)
                self._broadcast_stop_event = Event()
                t = Thread(target=self._broadcast, args=(self._broadcaster, self._broadcast_stop_event))
                t.start()

            if self._use_video_service:
                # start camera
                if self.camera:
                    self.camera.start_video_service()
        else:
            self.warning('No furnace configuration file located at {}'.format(p))

    # properties
    @property
    def furnace_env_humidity(self):
        if self.temp_hum:
            return self.temp_hum.humdity

    @property
    def furnace_env_temperature(self):
        if self.temp_hum:
            return self.temp_hum.temperature

    @property
    def furnace_setpoint(self):
        return self.get_setpoint()

    @property
    def furnace_process_value(self):
        return self.get_temperature()

    @property
    def feeder_position(self):
        if self.feeder:
            return self.feeder.position

    @property
    def funnel_position(self):
        if self.funnel:
            return self.funnel.position

    def get_heartbeat(self, data):
        return '{},{}'.format(time.time(), self._start_time)

    def get_furnace_summary(self, data):
        h2o_channel = None
        if isinstance(data, dict):
            h2o_channel = data.get('h2o_channel')

        s = {}
        if h2o_channel is not None:
            s['h2o_state'] = self.switch_controller.get_channel_state(h2o_channel)

        s['setpoint'] = self.get_setpoint(None)
        s['response'] = self.get_temperature(None)
        s['output'] = self.get_percent_output(None)
        return json.dumps(s)

    def get_percent_output(self, data):
        if self.controller:
            return self.controller.get_output(verbose=False)

    def get_full_summary(self):
        s = {'version': __version__}
        for attr in ('furnace_env_humidity', 'furnace_env_temperature',
                     'furnace_setpoint', 'furnace_process_value',
                     'feeder_position', 'funnel_position'):
            addr = PARAMETER_REGISTRY.get(attr)
            if addr:
                v = getattr(self, attr)
                s[addr] = v

        ss = []
        for k in self._switch_mapping:
            _, o, c = self.get_indicator_component_states(k)
            rs = self.get_channel_state(k)
            ss.append('{},s{},o{},c{}'.format(k, rs, o, c))

        s[PARAMETER_REGISTRY.get('switch_status')] = ';'.join(ss)
        return json.dumps(s)

    @debug
    def get_lab_humidity(self, data):
        if self.temp_hum:
            self.temp_hum.update()
            return self.temp_hum.humdity

    @debug
    def get_lab_temperature(self, data):
        if self.temp_hum:
            self.temp_hum.update()
            return self.temp_hum.temperature

    @debug
    def get_temperature(self, data):
        if self.controller:
            return self.controller.get_process_value(verbose=False)

    @debug
    def get_setpoint(self, data):
        if self.controller:
            return self.controller.process_setpoint

    @debug
    def get_magnets_state(self, data):
        return 0

    @debug
    def get_position(self, data):
        drive = self._get_drive(data)
        if drive:
            return drive.get_position()

    @debug
    def moving(self, data):
        drive = self._get_drive(data)
        if drive:
            return drive.moving()

    @debug
    def is_funnel_down(self, data):
        funnel = self.funnel
        if funnel:
            pos = funnel.read_position()
            return abs(pos - self._funnel_down) < self._funnel_tolerance

    @debug
    def is_funnel_up(self, data):
        funnel = self.funnel
        if funnel:
            pos = funnel.read_position()
            return abs(pos - self._funnel_up) < self._funnel_tolerance

    @debug
    def get_channel_state(self, data):
        """
        return the requested state of the channel
        @param data:
        @return:
        """
        if self.switch_controller:
            ch, inverted = self._get_switch_channel(data)
            result = self.switch_controller.get_channel_state(ch)
            if inverted:
                result = not result
            return result

    @debug
    def get_indicator_state(self, data):
        """
        return state of the indicator as a str, e.g open, close or Error: ...
        @param data:
        @return:
        """
        if self.switch_controller:
            args = self._get_indicator_info(data)
            return args[0]

    @debug
    def get_indicator_component_states(self, data):
        """
        return csv str of result, open_state, close_state
        @param data:
        @return:
        """
        if self.switch_controller:
            args = self._get_indicator_info(data)
            return ','.join([str(a) for a in args])

    @debug
    def get_di_state(self, data):
        if self.switch_controller:
            if isinstance(data, dict):
                di = data['name']
            else:
                di = data
            return self.switch_controller.get_channel_state(di)

    @debug
    def get_version(self, data):
        return __version__

    # setters
    @debug
    def set_frame_rate(self, data):
        if self.camera:
            self.camera.frame_rate = int(data)

    @debug
    def set_setpoint(self, data):
        if self.controller:
            if isinstance(data, dict):
                sp = data.get('setpoint', 0)
            else:
                sp = float(data)

            self.controller.process_setpoint = sp
            return 'OK'

    @debug
    def open_switch(self, data):
        if self.switch_controller:
            ch, inverted = self._get_switch_channel(data)
            if ch:
                self.switch_controller.set_channel_state(ch, False if inverted else True)
                return 'OK'

    @debug
    def close_switch(self, data):
        if self.switch_controller:
            ch, inverted = self._get_switch_channel(data)
            if ch:
                self.switch_controller.set_channel_state(ch, True if inverted else False)
                return 'OK'

    @debug
    def raise_funnel(self, data):
        if self.funnel:
            return self.funnel.move_absolute(self._funnel_up, block=False)

    @debug
    def lower_funnel(self, data):
        if self.funnel:
            return self.funnel.move_absolute(self._funnel_down, block=False)

    @debug
    def rotary_dumper_moving(self, data):
        if self.rotary_dumper:
            return self.rotary_dumper.is_moving()

    @debug
    def energize_magnets(self, data):
        if self._magnet_channels:
            if self.switch_controller:
                period = 3
                if data:
                    if isinstance(data, dict):

                        period = data.get('period', 3)
                    else:
                        period = data

                def func():
                    self._is_energized = True
                    prev = None
                    for m in self._magnet_channels:
                        self.switch_controller.set_channel_state(m, True)
                        if prev:
                            self.switch_controller.set_channel_state(prev, False)

                        prev = m
                        time.sleep(period)
                    self.switch_controller.set_channel_state(prev, False)
                    self._is_energized = False

                t = Thread(target=func)
                t.start()
        else:
            if self.rotary_dumper:
                nsteps = None
                rpm = None
                if data:
                    if isinstance(data, dict):
                        nsteps = data.get('nsteps', 3)
                        rpm = data.get('rpm')
                    else:
                        nsteps = data

                self._is_energized = True

                t = Thread(target = self.rotary_dumper.energize, args=(nsteps, rpm))
                t.start()
                # while self.rotary_dumper.is_energized():
                #     time.sleep(0.5)
                # self._is_energized = False
        return True

    @debug
    def is_energized(self, data):
        return self._is_energized

    @debug
    def denergize_magnets(self, data):
        self._is_energized = False
        if self._magnet_channels:
            if self.switch_controller:
                for m in self._magnet_channels:
                    self.switch_controller.set_channel_state(m, False)
        else:
            if self.rotary_dumper:
                nsteps = None
                if data:
                    if isinstance(data, dict):
                        nsteps = data.get('nsteps')
                    else:
                        nsteps = data

                t = Thread(target=self.rotary_dumper.denergize, args=(nsteps,))
                t.start()

        return True

    @debug
    def move_absolute(self, data):
        drive = self._get_drive(data)
        if drive:
            units = data.get('units', 'steps')
            velocity = data.get('velocity')
            return drive.move_absolute(data['position'], velocity=velocity, block=False, units=units)

    @debug
    def move_relative(self, data):
        drive = self._get_drive(data)
        if drive:
            units = data.get('units', 'steps')
            return drive.move_relative(data['position'], block=False, units=units)

    @debug
    def stop_drive(self, data):
        drive = self._get_drive(data)
        if drive:
            return drive.stop_drive()

    @debug
    def set_home(self, data):
        drive = self._get_drive(data)
        if drive:
            return drive.set_home()

    @debug
    def stalled(self, data):
        drive = self._get_drive(data)
        if drive:
            return drive.stalled()

    @debug
    def slew(self, data):
        drive = self._get_drive(data)
        if drive:
            scalar = data.get('scalar', 1.0)
            return drive.slew(scalar)

    @debug
    def start_jitter(self, data):
        drive = self._get_drive(data)
        if drive:
            turns = data.get('turns', 10)
            p1 = data.get('p1', 0.1)
            p2 = data.get('p2', 0.1)
            velocity = data.get('velocity', None)
            acceleration = data.get('acceleration', None)
            deceleration = data.get('deceleration', None)
            return drive.start_jitter(turns, p1, p2, velocity, acceleration, deceleration)

    @debug
    def stop_jitter(self, data):
        drive = self._get_drive(data)
        if drive:
            return drive.stop_jitter()

    @debug
    def set_pid(self, data):
        if isinstance(data, dict):
            data = data['pid']

        controller = self.controller
        if controller:
            return controller.set_pid_str(data)

    @debug
    def set_bakeout_setpoint(self, data):
        controller = self._get_bakeout_controller(data)
        if controller:
            value = data['setpoint']
            ret = controller.set_closed_loop_setpoint(value)

            # set_closed_loop_setpoint returns true if request and actual setpoints are greater than 0.01 different,
            # True == Failed to set setpoint
            # None == Succeeded to setpoint
            return 'OK' if not ret else 'Fail'

    @debug
    def get_bakeout_setpoint(self, data):
        controller = self._get_bakeout_controller(data)
        if controller:
            return controller.read_closed_loop_setpoint()

    @debug
    def get_bakeout_temp_and_power(self, data):
        controller = self._get_bakeout_controller(data)
        if controller:
            return controller.get_temp_and_power()

    @debug
    def set_bakeout_control_mode(self, data):
        controller = self._get_bakeout_controller(data)
        if controller:
            if isinstance(data, dict):
                mode = data['mode']
            else:
                mode = data
            return controller.set_control_mode(mode)

    @debug
    def get_bakeout_temperature(self, data):
        controller = self._get_bakeout_controller(data)
        if controller:
            return controller.get_temperature()

    @debug
    def get_gauge_pressure(self, data):
        controller, channel = self._get_gauge_controller(data)
        if controller:
            return controller.get_pressure(channel, force=True)

    # private
    def _get_gauge_controller(self, data):
        controller, channel = None, None

        if isinstance(data, dict):
            name = data['name']
        else:
            name, channel = data

        try:
            controller = getattr(self, name)
        except AttributeError:
            pass

        return controller, channel

    def _get_bakeout_controller(self, data):
        channel = data['channel']
        try:
            controller = getattr(self, 'bakeout_controller{}'.format(channel))
        except AttributeError:
            return 'Invalid bakeout channel {}, data={}'.format(channel, data)
        return controller

    def _get_indicator_info(self, data):
        """

        returns a 3-tuple (result, open_state, close_state)

        result: str  open, close or Error: ...
        open_state: bool
        close_state: bool

        @param data:
        @return:
        """
        def prep_channel(channel):
            inv = False
            if channel.startswith('i'):
                ch = channel[1:]
                inv = True
            return ch, inv

        if self.switch_controller:
            if isinstance(data, dict):
                alt_name = data['name']
            else:
                alt_name, _ = data
            alt_ch, inverted = self._get_switch_channel(alt_name)

            open_ch, close_ch, action = self._get_switch_indicator(data)

            if open_ch == 'inverted':
                oresult = not self.switch_controller.get_channel_state(alt_ch)
            else:
                ch, invert = prep_channel(open_ch)
                oresult = self.switch_controller.get_channel_state(ch)
                if invert:
                    oresult = not oresult

            if close_ch is None:
                cresult = None
            else:
                ch, invert = prep_channel(close_ch)
                cresult = self.switch_controller.get_channel_state(ch)
                if invert:
                    cresult = not cresult

            result = oresult
            if oresult == cresult:
                result = 'Error: OpenIndicator={}, CloseIndicator={}'.format(oresult, cresult)
            else:
                result = 'open' if result else 'closed'
            return result, oresult, cresult

    def _get_drive(self, data):
        drive = data.get('drive')
        if drive:
            try:
                return getattr(self, drive)
            except AttributeError:
                pass

    def _get_switch_channel(self, data):
        if isinstance(data, dict):
            name = data['name']
        else:
            name = data
        name = str(name)
        ch = self._switch_mapping.get(name, '')
        inverted = False
        if ',' in str(ch):
            ch, inverted = ch.split(',')
            inverted = to_bool(inverted)

        return ch, inverted

    def _get_switch_indicator(self, data):
        if isinstance(data, dict):
            name = data['name']
            action = data['action']
        else:
            name, action = data

        close_ch = None
        open_ch = self._switch_indicator_mapping.get(name)
        if open_ch == 'inverted':
            return open_ch, None, None

        if ',' in str(open_ch):
            def prep(ch):
                ch = ch.strip()
                if not ch or ch == '-':
                    ch = None
                return ch

            open_ch, close_ch = (prep(c) for c in open_ch.split(','))

        return open_ch, close_ch, action

    def _broadcast(self, bs, evt):
        i = 0
        while not evt.is_set():
            if not i % 10:
                bs.send_message(self.get_full_summary())
                i = -1
            else:
                bs.send_message('HeartBeat {}'.format(time.time()))
            i += 1
            time.sleep(2)

    # bootstrapping
    def _load_config(self, cd):
        self._use_video_service = cd.get('use_video_service', False)

        bs = cd.get('broadcast', None)
        if bs:
            self._use_broadcast_service = bs.get('enabled')
            self._broadcast_port = bs.get('port', 9000)

    def _load_rotary_dumper(self):
        pass

    def _load_magnets(self, m):
        self._magnet_channels = m

    def _load_funnel(self, f):
        if self.funnel:
            self._funnel_down = self.funnel.tosteps(f['down'])
            self._funnel_up = self.funnel.tosteps(f['up'])
            self._funnel_tolerance = f['tolerance']

    def _load_switch_mapping(self, m):
        self._switch_mapping = m

    def _load_switch_indicator_mapping(self, m):
        self._switch_indicator_mapping = m

    def _load_devices(self, devices):
        for dev in devices:
            self._load_device(dev)

    def _load_device(self, devname):
        self.debug('load device name={}'.format(devname))
        klass = DEVICES.get(devname)
        if klass:
            dev = klass(name=devname, configuration_dir_name='furnace')
            dev.bootstrap()

            setattr(self, devname, dev)
        else:
            self.warning('Invalid device {}'.format(devname))

# ============= EOF =============================================
