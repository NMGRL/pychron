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
from zaber_motion import Units

from pychron.hardware.motion_controller import MotionController
from pychron.hardware.axis import Axis

import os


class LegacyZaberAxis(Axis):
    device_id = None
    microstep_size = 0.1905
    device = None

    def get_position(self):
        steps = self.device.get_position()
        return self.convert_to_mm(steps)

    def convert_to_mm(self, steps):
        return float(steps * self.microstep_size / 1000.0)

    def convert_to_steps(self, mm):
        return int(mm * 1000 / self.microstep_size)

    def load(self, path):
        if not os.path.isfile(path):
            path = os.path.join(path, "{}axis.cfg".format(self.name))

        config = self.get_configuration(path)
        self.set_attribute(config, "sign", "Motion", "sign", cast="int", default=1)
        self.set_attribute(config, "device_id", "General", "device_id", cast="int")
        self.set_attribute(
            config, "microstep_size", "General", "microstep_size", cast="float"
        )
        self.set_attribute(config, "positive_limit", "Motion", "positive_limit", cast="float", default=50)


class ZaberAxis(LegacyZaberAxis):
    def get_position(self):
        mm = 0
        if self.device:
            mm = self.device.get_position(Units.LENGTH_MILLIMETRES)

        self.debug(f'get position {mm}, {self.device}')
        if self.sign == -1:
            mm = self.positive_limit - mm
        return mm

# ============= EOF =============================================
