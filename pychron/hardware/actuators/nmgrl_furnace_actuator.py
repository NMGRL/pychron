# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= enthought library imports =======================
import json

from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
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
from pychron.hardware.actuators import invert_trim_bool, get_valve_name, trim_bool, get_valve_address


class NMGRLFurnaceActuator(GPActuator):
    """
        Used to communicate with furnace switches
    """

    # @trim
    # def get_state_checksum(self, vkeys, verbose=False):
    #     cmd = 'GetStateChecksum {}'.format(','.join(vkeys))
    #     resp = self.ask(cmd, verbose=verbose)
    #     return resp
    #
    # @trim_bool
    # def get_lock_state(self, obj, verbose=False):
    #     cmd = 'GetValveLockState {}'.format(get_valve_name(obj))
    #     return self.ask(cmd, verbose=verbose)
    #
    # @trim
    # def get_owners_word(self, verbose=False):
    #     cmd = 'GetValveOwners'
    #     return self.ask(cmd, verbose=verbose)
    #
    # @trim
    # def get_state_word(self, verbose=False):
    #     cmd = 'GetValveStates'
    #     return self.ask(cmd, verbose=verbose)
    #
    # @trim
    # def get_lock_word(self, verbose=False):
    #     cmd = 'GetValveLockStates'
    #     return self.ask(cmd, verbose=verbose)

    @trim_bool
    def get_channel_state(self, obj, verbose=True):
        """
            Query the hardware for the channel state
        """
        cmd = 'GetChannelState {}'.format(get_valve_address(obj))
        return self.ask(cmd, verbose=verbose)

    @trim_bool
    def get_indicator_state(self, obj, action, verbose=True):
        cmd = json.dumps({'command': 'GetIndicatorState',
                          'name': get_valve_address(obj),
                          'action': action})

        # cmd = 'GetIndicatorState {},{}'.format(get_valve_address(obj), action)
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
            return self._check_actuate(obj, action)

    @trim_bool
    def _actuate(self, obj, action):
        """
            obj: valve object
            action: str,  "Open" or "Close"
        """
        if self.simulation:
            return True

        cmd = '{} {}'.format(action, get_valve_address(obj))
        return self.ask(cmd)

    def _check_actuate(self, obj, action):
        if not obj.check_actuation_enabled:
            return True

        if obj.check_actuation_delay:
            time.sleep(obj.check_actuation_delay)

        # state = action == 'Open'
        # chk = '1' if action == 'Close' else '0'
        result = self.get_indicator_state(obj, action)
        self.debug('check actuate action={}, result={}'.format(action, result))

        return result

# ============= EOF =====================================


# ============= EOF =============================================



