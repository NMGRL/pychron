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
from pychron.hardware.actuators.client_gp_actuator import ClientMixin
from pychron.hardware.actuators.gp_actuator import GPActuator


class PLC2000GPActuator(GPActuator, ClientMixin):
    def _actuate(self, obj, action):
        self._write_coil(int(obj.address), action.lower() == 'open')

    def get_channel_state(self, address, *args, **kw):
        resp = self._read_coils(int(address))
        return bool(resp.bits[0])

    def _read_coils(self, *args, **kw):
        if self.communicator:
            return self.communicator.read_coils(*args, **kw)

    def _write_coil(self, *args, **kw):
        if self.communicator:
            return self.communicator.write_coil(*args, **kw)

# ============= EOF =============================================
