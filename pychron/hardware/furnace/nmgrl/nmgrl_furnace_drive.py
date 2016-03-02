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
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class NMGRLFurnaceDrive(CoreDevice):

    def load_additional_args(self, config):
        self.set_attribute(config, 'drive_name', 'General', 'drive_name')
        return True

    def move_absolute(self, pos, units='steps'):
        d = {'position': pos, 'units': units, 'drive': self.drive_name}
        d = json.dumps(d)
        self.ask('MoveAbsolute {}'.format(d))

    set_position = move_absolute

    def move_relative(self, turns, units='steps'):
        d = {'position': turns, 'units': units, 'drive': self.drive_name}
        d = json.dumps(d)
        self.ask('MoveRelative {}'.format(d))

    def stop_drive(self):
        d = {'drive': self.drive_name}
        d = json.dumps(d)
        self.ask('StopDrive {}'.format(d))

    def slew(self, scalar):
        d = {'scalar': scalar, 'drive': self.drive_name}
        d = json.dumps(d)
        self.ask('Slew {}'.format(d))

    def moving(self):
        d = {'drive': self.drive_name}
        d = json.dumps(d)
        return self.ask('Moving {}'.format(d))

    def get_position(self, units='steps'):
        d = {'drive': self.drive_name, 'units':units}
        d = json.dumps(d)
        return self.ask('GetPosition {}'.format(d))

# ============= EOF =============================================



