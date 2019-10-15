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

from pychron.hardware.actuators import get_switch_address, trim_affirmative
from pychron.hardware.actuators.gp_actuator import GPActuator


class ASCIIGPActuator(GPActuator):
    affirmative = 'OK'
    close_cmd = 'Close'
    open_cmd = 'Open'
    delimiter = ' '
    state_open = 'True'
    state_cmd = 'GetValveState'

    def get_channel_state(self, obj, verbose=False, **kw):
        """
        """

        cmd = '{} {}'.format(self.state_cmd, get_switch_address(obj))

        s = self.ask(cmd, verbose=verbose)

        if s is not None:
            return s.strip() == self.state_open

    @trim_affirmative
    def _actuate(self, obj, action):
        self.debug('Actuate {} {}'.format(obj, action))
        state = action.lower() == 'open'
        cmd = self.open_cmd if state else self.close_cmd

        if callable(cmd):
            cmd = cmd(get_switch_address(obj))
        else:
            cmd = '{}{}{}'.format(cmd, self.delimiter, get_switch_address(obj))

        r = self.ask(cmd, verbose=True)
        return r

# ============= EOF =============================================
