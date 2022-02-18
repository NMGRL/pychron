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
from traits.api import Dict

class MCCGPActuator(GPActuator, ClientMixin):
    local_states = Dict
    def _actuate(self, obj, action):
        addr = obj.address
        state = action.lower() == 'open'
        print('actuate. write digital out {} {}'.format(addr, state))
        self.communicator.d_out(addr, state)
        self.local_states[addr] = state
        return True

    def get_channel_state(self, address, *args, **kw):
        print(self.local_states)
        return self.local_states.get(address, False)
        #return self.communicator.d_in(address)

# ============= EOF =============================================
