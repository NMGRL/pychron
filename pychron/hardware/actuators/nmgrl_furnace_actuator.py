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
from pychron.core.communication_helper import trim_bool
from pychron.core.helpers.strtools import to_bool
from pychron.hardware.actuators import get_valve_address


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

    def get_indicator_state(self, obj, action='open', verbose=True):
        """
        returns True if open and False if closed.

        :param obj:
        :param action:
        :param verbose:
        :return:
        """
        cmd = json.dumps({'command': 'GetIndicatorState',
                          'name': get_valve_address(obj),
                          'action': action})
        resp = self.ask(cmd, verbose=True)

        # if action == 'open':
        # print 'aa', resp, action
        if resp:
            resp = resp.strip()
            if resp == 'open':
                return True
            elif resp == 'closed':
                return False
            # resp = to_bool(resp.strip())
            # resp = resp.strip()
            # if action == 'open' and resp == 'open':
            #     return True
            # elif action == 'closed' and resp == 'closed':
            #     return False
            # elif action == 'closed' and resp == 'open':
            #     return True
            # elif action == 'open' and resp == 'closed':
            #     return False

                # print 'bb', resp
                # # # if close indicator is True and checking for closed return False
                # if resp and action != 'open':
                # #     resp = False
                # # print 'cc', obj, resp
                # return resp

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
        result = self.get_indicator_state(obj, action)
        self.debug('check actuate action={}, result={}'.format(action, result))

        if action == 'Close':
            result = not result

        return result

# ============= EOF =====================================


# ============= EOF =============================================
