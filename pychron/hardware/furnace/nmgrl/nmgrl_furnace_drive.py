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
from traits.api import Str, Int
# ============= standard library imports ========================
import json
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class NMGRLFurnaceDrive(CoreDevice):
    drive_name = Str
    velocity = Int(10000)

    def load_additional_args(self, config):
        self.set_attribute(config, 'drive_name', 'General', 'drive_name')
        return True

    def move_absolute(self, pos, units='steps', velocity=None):
        self.ask(self._build_command('MoveAbsolute', position=pos, units=units, velocity=velocity))

    def set_position(self, *args, **kw):
        kw['units'] = 'turns'
        kw['velocity'] = self.velocity
        self.move_absolute(*args, **kw)

    def move_relative(self, pos, units='steps'):
        self.ask(self._build_command('MoveRelative', position=pos, units=units))

    def stop_drive(self):
        self.ask(self._build_command('StopDrive'))

    def slew(self, scalar):
        self.ask(self._build_command('Slew', scalar=scalar))

    def moving(self):
        return self.ask(self._build_command('Moving'))

    def get_position(self, units='steps'):
        return self.ask(self._build_command('GetPosition', units=units))

    def start_jitter(self, turns, p1, p2, velocity):
        return self.ask(self._build_command('StartJitter', turns=turns, p1=p1, p2=p2, velocity=velocity))

    def stop_jitter(self):
        return self.ask(self._build_command('StopJitter'))

    def _build_command(self,cmd, **kw):
        kw['drive'] = self.drive_name
        kw['command'] = cmd
        return json.dumps(kw)
# ============= EOF =============================================



