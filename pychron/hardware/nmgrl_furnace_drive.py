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

    def move_relative(self, turns, convert_turns=False):
        d = {'turns': turns, 'convert_turns': convert_turns}
        d = json.dumps(d)
        self.ask('MoveRelative {}'.format(d))

    def stop_drive(self):
        pass

    def slew(self, modifier):
        pass

    def set_position(self, pos):
        d = {'position': pos, 'drive': self.drive_name}
        d = json.dumps(d)
        self.ask('SetPosition {}'.format(d))

    def moving(self):
        d = {'drive': self.drive_name}
        d = json.dumps(d)
        return self.ask('Moving {}'.format(d))


# ============= EOF =============================================



