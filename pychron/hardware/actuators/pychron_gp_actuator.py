# ===============================================================================
# Copyright 2011 Jake Ross
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

#========== standard library imports ==========
import time

#========== local library imports =============
from gp_actuator import GPActuator
from pychron.core.helpers.filetools import to_bool


def get_valve_name(obj):
    if isinstance(obj, (str, int)):
        addr = obj
    else:
        addr = obj.name.split('-')[1]
    return addr


class PychronGPActuator(GPActuator):
    """
        Used to communicate with PyValve valves
    """

    def get_state_checksum(self, vkeys, verbose=False):
        cmd = 'GetStateChecksum {}'.format(','.join(vkeys))
        resp = self.ask(cmd, verbose=verbose)
        return resp

    def get_lock_state(self, obj):
        cmd = 'GetValveLockState {}'.format(get_valve_name(obj))
        resp = self.ask(cmd)
        if resp is not None:
            resp = resp.strip()
            return to_bool(resp)

    def get_owners_word(self, verbose=False):
        cmd = 'GetValveOwners'
        resp = self.ask(cmd, verbose=verbose)
        return resp

    def get_state_word(self, verbose=False):
        cmd = 'GetValveStates'
        resp = self.ask(cmd, verbose=verbose)
        return resp

    def get_lock_word(self, verbose=False):
        cmd = 'GetValveLockStates'
        resp = self.ask(cmd, verbose=verbose)
        return resp

    def get_channel_state(self, obj):
        """
            Query the hardware for the channel state
        """
        cmd = 'GetValveState {}'.format(get_valve_name(obj))
        resp = self.ask(cmd)
        if resp is not None:
            resp = to_bool(resp.strip())

        return resp

    def close_channel(self, obj, excl=False):
        """
            Close the channel
            obj: valve object

            return True if actuation completed successfully
        """
        return self._actuate(obj, 'Close')


    def open_channel(self, obj):
        """
            Open the channel
            obj: valve object

            return True if actuation completed successfully
        """
        return self._actuate(obj, 'Open')

    def _actuate(self, obj, action):
        """
            obj: valve object
            action: str,  "Open" or "Close"
        """
        if self.simulation:
            return True

        state = action == 'Open'
        cmd = '{} {}'.format(action, get_valve_name(obj))
        resp = self.ask(cmd)
        if resp:
            if resp.lower().strip() == 'ok':
                time.sleep(0.05)
                resp = self.get_channel_state(obj) == state
        return resp

# ============= EOF =====================================
