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
from zaber_motion import Units
from pychron.hardware.axis import Axis

import os


class ZaberAxis(Axis):
    device_id = None
    def load(self, path):
        if not os.path.isfile(path):
            path = os.path.join(path, '{}axis.cfg'.format(self.name))

        config = self.get_configuration(path)
        self.set_attribute(config, 'device_id', 'General', 'device_id', cast='int')

# ============= EOF =============================================
