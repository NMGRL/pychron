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

# ========== standard library imports ==========
import time

# ========== local library imports =============
from gp_actuator import GPActuator
from pychron.hardware.actuators import trim, trim_bool, get_valve_name


class PychronGPActuator(GPActuator):
    """
        Used to communicate with PyValve valves
    """

    @trim
    def get_state_checksum(self, vkeys, verbose=False):
        cmd = 'GetStateChecksum {}'.format(','.join(vkeys))
        resp = self.ask(cmd, verbose=verbose)
        return resp

    @trim_bool
    def get_lock_state(self, obj, verbose=False):
        cmd = 'GetValveLockState {}'.format(get_valve_name(obj))
        return self.ask(cmd, verbose=verbose)

    @trim
    def get_owners_word(self, verbose=False):
        cmd = 'GetValveOwners'
        return self.ask(cmd, verbose=verbose)

    @trim
    def get_state_word(self, verbose=False):
        cmd = 'GetValveStates'
        return self.ask(cmd, verbose=verbose)

    @trim
    def get_lock_word(self, verbose=False):
        cmd = 'GetValveLockStates'
        return self.ask(cmd, verbose=verbose)

    @trim_bool
    def get_channel_state(self, obj, verbose=True):
        """
            Query the hardware for the channel state
        """
        cmd = 'GetValveState {}'.format(get_valve_name(obj))
        return self.ask(cmd, verbose=verbose)

    def close_channel(self, obj, excl=False):
        """
            Close the channel
            obj: valve object

            return True if actuation completed successfully
        """
        return self.actuate(obj, 'Close')

    def open_channel(self, obj):
        """
            Open the channel
            obj: valve object

            return True if actuation completed successfully
        """
        return self.actuate(obj, 'Open')

    def actuate(self, obj, action):
        if self._actuate(obj, action):
            time.sleep(0.05)
            return self._check_actuate(obj, action)

    @trim_bool
    def _actuate(self, obj, action):
        """
            obj: valve object
            action: str,  "Open" or "Close"
        """
        if self.simulation:
            return True

        cmd = '{} {}'.format(action, get_valve_name(obj))
        return self.ask(cmd)

    def _check_actuate(self, obj, action):
        state = action == 'Open'
        return self.get_channel_state(obj) == state

# ============= EOF =====================================
