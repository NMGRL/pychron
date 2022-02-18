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
import json
import os
from pychron.paths import paths

class MCCGPActuator(GPActuator, ClientMixin):
    def __init__(self, *args, **kw):
        super(MCCGPActuator, self).__init__(*args, **kw)
        self._persistence_path = os.path.join(paths.appdata_dir, 'valve_states.json')
        self._local_states = {}

    def _actuate(self, obj, action):
        addr = obj.address
        state = action.lower() == 'open'
        print('actuate. write digital out {} {}'.format(addr, state))
        self.communicator.d_out(addr, state)
        self._local_states[addr] = state

        self._dump_states()
        return True

    def _dump_states(self):
        p = self._persistence_path
        with open(p, 'w') as wfile:
            json.dump(self._local_states, wfile)

    def _load_states(self):
        p = self._persistence_path
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                self._local_states = json.load(rfile)

    def get_channel_state(self, address, *args, **kw):

        read_states_from_mcc = False
        if read_states_from_mcc:
            ret = self.communicator.d_in(address)
        else:
            if not self._local_states:
                self._load_states()
            ret = self._local_states.get(address, False)

        #print(self.local_states)
        #return self.local_states.get(address, False)
        return ret

# ============= EOF =============================================
