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
        handle = self.communicator.handle
        handle.write_coil(int(obj.address), action.lower() == 'open')

    def get_channel_state(self, obj, *args, **kw):
        handle = self.communicator.handle
        resp = handle.read_coils(int(obj.address), 1)
        return resp.bits[0]

# ============= EOF =============================================
