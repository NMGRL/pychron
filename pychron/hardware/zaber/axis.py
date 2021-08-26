# ===============================================================================
# Copyright 2021 ross
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
from traits.api import Str, CInt, Enum

from pychron.hardware.motion_controller import MotionController
from pychron.hardware.axis import Axis

import os


class ZaberAxis(Axis):
    device_id = None
    microstep_size = 0.1905
    device = None

    def get_position(self):
        steps = self.device.get_position()
        mm = self.convert_to_mm(steps)
        return mm

    def convert_to_mm(self, steps):
        return float(steps*self.microstep_size/1000.)

    def convert_to_steps(self, mm):
        return int(mm*1000/self.microstep_size)

    def load(self, path):
        if not os.path.isfile(path):
            path = os.path.join(path, '{}axis.cfg'.format(self.name))

        config = self.get_configuration(path)
        self.set_attribute(config, 'device_id', 'General', 'device_id', cast='int')
        self.set_attribute(config, 'microstep_size', 'General', 'microstep_size', cast='float')
# ============= EOF =============================================
