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
from pychron.hardware.core.core_device import CoreDevice
from traits.api import Button, Bool, Property, Float


class Pyrometer(CoreDevice):
    temperature = Float

    pointer = Button
    pointing = Bool
    pointer_label = Property(depends_on='pointing')

    def read_temperature(self):
        raise NotImplementedError

    def set_laser_pointer(self, onoff):
        raise NotImplementedError

    def _get_pointer_label(self):
        """
        """
        return 'Pointer ON' if not self.pointing else 'Pointer OFF'

    def _pointer_fired(self):
        """
        """
        self.pointing = not self.pointing

        self.set_laser_pointer(self.pointing)

# ============= EOF =============================================
