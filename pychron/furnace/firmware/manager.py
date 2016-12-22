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

# ============= enthought library imports =======================
# ============= standard library imports ========================
import json
from threading import Thread, Event

from cStringIO import StringIO
import time
from cPickle import dumps
import struct
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_bool
from pychron.furnace.firmware import PARAMETER_REGISTRY, __version__
from pychron.hardware.dht11 import DHT11
from pychron.hardware.eurotherm.headless import HeadlessEurotherm
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
           'backout1': HeadlessWatlowEZZone,
           'backout2': HeadlessWatlowEZZone}


def debug(func):
    def wrapper(obj, data):
        obj.debug('------ {}, data={}'.format(func.__name__, data))
        r = func(obj, data)
        obj.debug('------ result={}'.format(r))
        return r

    return wrapper


class FirmwareManager(HeadlessLoggable):
    controller = None
    switch_controller = None
    funnel = None
    feeder = None
    temp_hum = None
    camera = None

    _switch_mapping = None
    _switch_indicator_mapping = None
    _is_energized = False

    _use_video_service = False
    _use_broadcast_service = False
    _broadcast_port = 9000
    _start_time = 0
    _broadcaster = None
    _broadcast_stop_event = None

    def bootstrap(self, **kw):
        self._start_time = time.time()
        p = paths.furnace_firmware
        with open(p, 'r') as rfile:
            yd = yaml.load(rfile)

        self._load_config(yd['config'])
        self._load_devices(yd['devices'])
        self._load_switch_mapping(yd['switch_mapping'])
        self._load_switch_indicator_mapping(yd['switch_indicator_mapping'])
        self._load_funnel(yd['funnel'])
        self._load_magnets(yd['magnets'])

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

    # getters
    # @debug
    # def get_jpeg(self, data):
    #     quality = 100
    #     if isinstance(data, dict):
    #         quality = data['quality']
    #
    #     memfile = StringIO()
    #     self.camera.capture(memfile, name=None, quality=quality)
    #     memfile.seek(0)
    #     return json.dumps(memfile.read())
    #
    # def get_image_array(self, data):
    #     if self.camera:
    #         im = self.camera.get_image_array()
    #         if im is not None:
    #             imstr = im.dumps()
    #             return '{:08X}{}'.format(len(imstr), imstr)

    def get_heartbeat(self):
        return '{},{}'.format(time.time(), self._start_time)

    def get_furnace_summary(self):
        return 'Not yet implemented'

    def get_percent_output(self):
        if self.controller:
            return self.controller.get_output()

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
        return dumps(s)

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
            return self.controller.get_process_value()

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
        if self.switch_controller:
            ch, inverted = self._get_switch_channel(data)
            result = self.switch_controller.get_channel_state(ch)
            if inverted:
                result = not result
            return result

    @debug
    def get_indicator_state(self, data):
        if self.switch_controller:
            args = self._get_indicator_info(data)
            return args[0]

    @debug
    def get_indicator_component_states(self, data):
        if self.switch_controller:
            args = self._get_indicator_info(data)
            return ','.join(args)

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
    def energize_magnets(self, data):
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
            return True

    @debug
    def is_energized(self):
        return self._is_energized

    @debug
    def denergize_magnets(self, data):
        self._is_energized = False
        if self.switch_controller:
            for m in self._magnet_channels:
                self.switch_controller.set_channel_state(m, False)
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
        controller = self._get_gauge_controller(data)
        if controller:
            c = self._get_gauge_channel(data)
            return controller.get_pressue(c)

    # private
    def _get_gauge_channel(self, data):
        gauge_id = data['gauge_id']

    def _get_gauge_controller(self, data):
        pass

    def _get_bakeout_controller(self, data):
        channel = data['channel']
        try:
            controller = getattr(self, 'bakeout_controller{}'.format(channel))
        except AttributeError:
            return 'Invalid bakeout channel {}, data={}'.format(channel, data)
        return controller

    def _get_indicator_info(self, data):
        if self.switch_controller:
            if isinstance(data, dict):
                alt_name = data['name']
            else:
                alt_name, _ = data
            alt_ch, inverted = self._get_switch_channel(alt_name)

            open_ch, close_ch, action = self._get_switch_indicator(data)
            #print 'ffffffff {} {} {}'.format(data, open_ch, close_ch)
            if open_ch is None:
                oresult = self.get_channel_state(alt_ch)
                if inverted:
                    oresult = not oresult
            else:
                invert = False
                if open_ch.startswith('i'):
                    open_ch = open_ch[1:]
                    invert = True
                oresult = self.switch_controller.get_channel_state(open_ch)
                #print 'gggggg {} {} {}'.format(invert, open_ch, oresult)
                if invert:
                    oresult = not oresult

            if close_ch is None:
                #cresult = self.get_channel_state(alt_ch)
                #if inverted:
                #    cresult = not cresult
                cresult = None
            else:
                invert = False
                if close_ch.startswith('i'):
                    close_ch = close_ch[1:]
                    invert = True

                cresult = self.switch_controller.get_channel_state(close_ch)
                if invert:
                    cresult = not cresult

            result = oresult
            if oresult == cresult:
                result = 'Error: OpenIndicator={}, CloseIndicator={}'.format(oresult, cresult)
            else:
                #if inverted:
                #    result = not result

                result = 'open' if result else 'closed'
            #print 'result={}, oresult={}, cresult={}'.format(result, oresult, cresult)
            return result, oresult, cresult

            # oresult = None
            # cresult = None
            # if action == 'open' and open_ch is None:
            #     result = self.get_channel_state(alt_ch)
            # else:
            #     oresult = False if action != 'open' else True
            #     if open_ch:
            #         oresult = self.switch_controller.get_channel_state(open_ch)
            #
            #     cresult = True if action != 'open' else False
            #     if close_ch:
            #         cresult = self.switch_controller.get_channel_state(close_ch)
            #
            #     if action == 'open':
            #         result = oresult and not cresult
            #     else:
            #         result = not oresult and cresult
            #
            # # if ch is None:
            # #     result = self.get_channel_state(alt_ch)
            # # else:
            # #     result = self.switch_controller.get_channel_state(ch)
            #
            # self.debug('indicator state {}, invert={} Open Indicator={}, Close Indicator={}'.format(result, inverted,
            #                                                                                         oresult,
            #                                                                                         cresult))
            # if inverted:
            #     result = not result
            #
            # if action == 'open' and result:
            #     result = 'open'
            # else:
            #     result = 'closed'
            #
            # return result, oresult, cresult

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

        ch = self._switch_mapping.get(name, '')
        inverted = False
        if ',' in str(ch):
            ch, inverted = ch.split(',')
            inverted = to_bool(inverted)

        self.debug('get switch channel {} {}'.format(name, ch))
        return ch, inverted

    def _get_switch_indicator(self, data):
        if isinstance(data, dict):
            name = data['name']
            action = data['action']
        else:
            name, action = data

        close_ch = None
        open_ch = self._switch_indicator_mapping.get(name)
        self.debug('get switch indicator channel {} {}'.format(name, open_ch))

        if ',' in str(open_ch):
            def prep(ch):
                ch = ch.strip()
                if not ch or ch == '-':
                    ch = None
                return ch

            open_ch, close_ch = map(prep, open_ch.split(','))

            # ch = o if action.lower() == 'open' else c
            # if not ch or ch == '-':
            #     ch = None

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
