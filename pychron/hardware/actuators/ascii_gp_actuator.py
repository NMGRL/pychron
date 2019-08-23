# ===============================================================================
# Copyright 2019 ross
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

from pychron.globals import globalv
from pychron.hardware.actuators import get_switch_address
from pychron.hardware.actuators.gp_actuator import GPActuator


def trim_affirmative(func):
    def wrapper(obj, *args, **kw):
        r = func(obj, *args, **kw)
        if r is None and globalv.communication_simulation:
            r = True
        else:
            r = r.strip() == obj._affirmative
        return r

    return wrapper


class ASCIIGPActuator(GPActuator):
    _affirmative = 'OK'
    _close_cmd = 'Close'
    _open_cmd = 'Open'
    _delimiter = ''
    _state_open = 'True'
    _state_cmd = 'GetValveState'

    def get_channel_state(self, obj, verbose=False, **kw):
        """
        """

        cmd = '{} {}'.format(self._state_cmd, get_switch_address(obj))

        s = self.ask(cmd, verbose=verbose)

        if s is not None:
            return s.strip() == self._state_open

    @trim_affirmative
    def _actuate(self, obj, action):
        state = action == 'Open'
        cmd = self._open_cmd if state else self._close_cmd
        cmd = '{}{}{}'.format(cmd, self._delimiter, get_switch_address(obj))
        r = self.ask(cmd)
        return r

# ============= EOF =============================================
