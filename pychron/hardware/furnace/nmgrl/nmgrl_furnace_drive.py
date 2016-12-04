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
from traits.api import Str, Int, Float
# ============= standard library imports ========================
import time
import json
# ============= local library imports  ==========================
from pychron.core.communication_helper import trim_bool
from pychron.hardware.core.core_device import CoreDevice


class NMGRLFurnaceDrive(CoreDevice):
    drive_name = Str
    velocity = Int(1000)

    jvelocity = Int
    jacceleration = Int
    jdeceleration = Int
    jperiod1 = Float
    jperiod2 = Float
    jturns = Float
    drive_sign = Int(1)

    def load_additional_args(self, config):
        self.set_attribute(config, 'drive_name', 'General', 'drive_name')
        self.set_attribute(config, 'velocity', 'Motion', 'velocity', cast='int')
        self.set_attribute(config, 'drive_sign', 'Motion', 'drive_sign', cast='int', default=1)

        self.set_attribute(config, 'jvelocity', 'Jitter', 'velocity', cast='int')
        self.set_attribute(config, 'jacceleration', 'Jitter', 'acceleration', cast='int')
        self.set_attribute(config, 'jdeceleration', 'Jitter', 'deceleration', cast='int')
        self.set_attribute(config, 'jperiod1', 'Jitter', 'period1', cast='float')
        self.set_attribute(config, 'jperiod2', 'Jitter', 'period2', cast='float')
        self.set_attribute(config, 'jturns', 'Jitter', 'turns', cast='float')

        return True

    def move_absolute(self, pos, units='steps', velocity=None, block=False):
        pos *= self.drive_sign
        self.ask(self._build_command('MoveAbsolute', position=pos, units=units, velocity=velocity))
        if block:
            self._block()

    def set_position(self, *args, **kw):
        kw['units'] = 'turns'
        kw['velocity'] = self.velocity
        self.move_absolute(*args, **kw)

    def move_relative(self, pos, units='steps'):
        pos *= self.drive_sign
        self.ask(self._build_command('MoveRelative', position=pos, units=units))

    def set_home(self):
        self.ask(self._build_command('SetHome'))

    def stop_drive(self):
        self.ask(self._build_command('StopDrive'))

    def slew(self, scalar):
        self.ask(self._build_command('Slew', scalar=scalar))

    @trim_bool
    def stalled(self):
        return self.ask(self._build_command('Stalled'))

    def moving(self):
        return self.ask(self._build_command('Moving')) == 'OK'

    def get_position(self, units='steps'):
        pos = self.ask(self._build_command('GetPosition', units=units))
        if pos:
            if pos != 'No Response':
                try:
                    pos = float(pos)
                    pos *= self.drive_sign
                except ValueError:
                    pos = None

            return pos

    def start_jitter(self, turns=None, p1=None, p2=None, **kw):

        if 'acceleration' not in kw:
            kw['acceleration'] = self.jacceleration
        if 'deceleration' not in kw:
            kw['deceleration'] = self.jdeceleration
        if 'velocity' not in kw:
            kw['velocity'] = self.jvelocity

        if turns is None:
            turns = self.jturns
        if p1 is None:
            p1 = self.jperiod1
        if p2 is None:
            p2 = self.jperiod2

        return self.ask(self._build_command('StartJitter', turns=turns, p1=p1, p2=p2, **kw))

    def stop_jitter(self):
        return self.ask(self._build_command('StopJitter'))

    def write_jitter_config(self):
        config = self.get_configuration()
        section = 'Jitter'
        for opt in ('jvelocity', 'jacceleration', 'jdeceleration', 'jperiod1', 'jperiod2', 'jturns'):
            config.set(section, opt[1:], getattr(self, opt))
        self.write_configuration(config)

    # private
    def _build_command(self, cmd, **kw):
        kw['drive'] = self.drive_name
        kw['command'] = cmd
        return json.dumps(kw)

    def _block(self, delay=None, timeout=100, period=1):
        st = time.time()
        if delay > 1:
            time.sleep(0.5)
            for i in range(3):
                mb = self.moving()
                if mb:
                    break
                time.sleep(0.1)
            else:
                return

        if delay:
            delay -= (time.time() - st)
            if delay > 0:
                time.sleep(delay)

        st = time.time()
        cnt = 0
        while time.time() - st < timeout:
            mb = self.moving()
            if not mb:
                cnt += 1
            else:
                cnt = 0

            pp = period
            if cnt:
                pp /= float(1 + cnt)

            if cnt > 2:
                break

            time.sleep(max(0.05, pp))
        else:
            self.debug('move timed out after {}s'.format(timeout))

# ============= EOF =============================================
