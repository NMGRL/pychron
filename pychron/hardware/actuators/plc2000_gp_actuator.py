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
try:
    from pymodbus.exceptions import ModbusIOException
except ImportError:
    pass

from pychron.hardware.actuators.client_gp_actuator import ClientMixin
from pychron.hardware.actuators.gp_actuator import GPActuator
from pychron.hardware.core.modbus import ModbusMixin


class PLC2000GPActuator(GPActuator, ModbusMixin, ClientMixin):
    """
    :::
    name: PLC2000 GP Actuator
    description: AutomationDirect.com PLC
    website: https://automationdirect.com

    """

    def _actuate(self, obj, action):
        addr = int(obj.address) - 1
        state = action.lower() == "open"
        self.debug("actuate. write coil {} {}".format(addr, state))

        self._write_coil(addr, state)
        return True

    def get_channel_state(self, obj, *args, **kw):
        try:
            address = obj.address
        except (ValueError, AttributeError):
            address = int(obj)

        resp = self._read_coils(int(address) - 1, 1)
        try:
            return bool(resp.bits[0])
        except ModbusIOException:
            self.debug_exception()


# ============= EOF =============================================
