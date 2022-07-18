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
from traits.api import provides

from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.ifiberlight import IFiberLight
from pychron.hardware.labjack.base_u3_lv import BaseU3LV


@provides(IFiberLight)
class U3FiberLight(BaseU3LV, CoreDevice):
    """
    configure DIO Mapping. need to map "power" to a channel e.g
    [DIOMapping]
    power=FIO3

    [AnalogMapping]
    intensity=0

    """

    dac_id = 0

    def load_additional_args(self, config):
        BaseU3LV.load_additional_args(self, config)

        self.set_attribute(
            config,
            "dac_id",
            "AnalogMapping",
            "intensity",
            default=0,
            optional=True,
            cast="int",
        )
        return True

    def power_on(self):
        self._power(True)

    def power_off(self):
        self._power(False)

    def set_intensity(self, v):
        self.set_dac_channel(self.dac_id, 5 * v)

    def read_intensity(self):
        return self.read_adc_channel(self.dac_id)

    def read_state(self):
        return self.get_channel_state("power")

    def _power(self, state):
        self.set_channel_state("power", state)


# ============= EOF =============================================
