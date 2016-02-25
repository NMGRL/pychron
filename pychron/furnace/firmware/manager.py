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
from threading import Thread
import time
import yaml
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.eurotherm.headless import HeadlessEurotherm
from pychron.hardware.labjack.headless_u3_lv import HeadlessU3LV
from pychron.headless_loggable import HeadlessLoggable
from pychron.paths import paths

DEVICES = {'controller': HeadlessEurotherm,
           'switch_controller': HeadlessU3LV}
           # 'funnel': MDriveMotor,
           # 'feeder': MDriveMotor}


class FirmwareManager(HeadlessLoggable):
    controller = None
    switch_controller = None
    funnel = None
    feeder = None

    def bootstrap(self, **kw):
        p = paths.furnace_firmware
        with open(p, 'r') as rfile:
            yd = yaml.load(rfile)

        self._load_devices(yd['devices'])
        self._load_switch_mapping(yd['switch_mapping'])
        self._load_funnel(yd['funnel'])
        self._load_magnets(yd['magnets'])

    def _load_magnets(self, m):
        self._magnet_channels = m

    def _load_funnel(self, f):
        self._funnel_down = f['down']
        self._funnel_up = f['up']
        self._funnel_tolerance = f['tolerance']

    def _load_switch_mapping(self, m):
        self._switch_mapping = m

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

    # getters
    def get_temperature(self, data):
        self.debug('----- get temperature')
        return 0.1

    def get_setpoint(self, data):
        self.debug('----- get setpoint')
        return 0

    def get_magnets_state(self, data):
        self.debug('----- get magnets state')
        return 0

    def get_position(self, data):
        self.debug('----- get position')
        drive = self._get_drive(data)
        if drive:
            return drive.read_position()

    def moving(self, data):
        self.debug('----- moving')
        drive = self._get_drive(data)
        if drive:
            return drive.moving()

    def is_funnel_down(self, data):
        self.debug('----- is_funnel_down')
        funnel = self.funnel
        if funnel:
            pos = funnel.read_position()
            return abs(pos - self._funnel_down) < self._funnel_tolerance

    def is_funnel_up(self, data):
        self.debug('----- is_funnel_up')
        funnel = self.funnel
        if funnel:
            pos = funnel.read_position()
            return abs(pos - self._funnel_up) < self._funnel_tolerance

    def get_channel_state(self, data):
        self.debug('----- channel state data={}'.format(data))
        if self.switch_controller:
            ch = self._get_switch_channel(data)

            return self.switch_controller.get_channel_state(ch)

    # setters
    def set_setpoint(self, data):
        self.debug('----- set setpoint data={}'.format(data))
        return

    def open_switch(self, data):
        self.debug('----- open switch data={}'.format(data))
        if self.switch_controller:
            ch = self._get_switch_channel(data)
            if ch:
                self.switch_controller.set_channel_state(ch, True)
                return 'OK'

    def close_switch(self, data):
        self.debug('----- close switch data={}'.format(data))
        if self.switch_controller:
            ch = self._get_switch_channel(data)
            if ch:
                self.switch_controller.set_channel_state(ch, False)
                return 'OK'

    def raise_funnel(self, data):
        self.debug('----- raise funnel')
        if self.funnel:
            return self.funnel.move_absolute(self._funnel_up)

    def lower_funnel(self, data):
        self.debug('----- lower funnel')
        if self.funnel:
            return self.funnel.move_absolute(self._funnel_down)

    def energize_magnets(self, data):
        self.debug('----- energize magnets')
        if self.switch_controller:
            def func():
                for m in self._magnet_channels:
                    self.switch_controller.set_channel_state(m, True)
                    time.sleep(1)

            t = Thread(target=func)
            t.start()
            return True

    def denergize_magnets(self, data):
        self.debug('----- denergize magnets')
        if self.switch_controller:
            for m in self._magnet_channels:
                self.switch_controller.set_channel_state(m, False)
            return True

    def move_absolute(self, data):
        self.debug('----- move absolute data={}'.format(data))
        drive = self._get_drive(data)
        if drive:
            drive.move_absolute(data['position'])

    def move_relative(self, data):
        self.debug('----- move relative data={}'.format(data))
        drive = self._get_drive(data)
        if drive:
            convert_turns = data.get('convert_turns', False)
            drive.move_absolute(data['position'], convert_turns=convert_turns)

    # private
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

        ch = self._switch_mapping.get(name)
        self.debug('get switch channel {} {}'.format(name, ch))
        return ch

# ============= EOF =============================================
