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
from pychron.hardware.agilent.agilent_mixin import AgilentMixin


class AgilentMultifunction(GPActuator, AgilentMixin):
    """

    Agilent 34907A

    """
    _state_word = None

    def get_channel_state(self, obj, verbose=False, **kw):
        addr = get_switch_address(obj)
        if self._read_state_word(addr[0]):
            return bool(self._state_word[int(addr)])

    def _read_state_word(self, slot, channel='01'):
        """
        state word is a list of 16 bits
        return True if read properly

        :return:
        """
        cmd = 'SENS:DIG:DATA:WORD? (@{}{})'.format(slot, channel)

        resp = self.ask(cmd)
        if resp is None:
            if globalv.communication_simulation:
                self._state_word = [0,]*16
                return True
        else:
            resp = resp.strip()
            if resp:
                word = '{:016b}'.format(int(resp))
                if self.invert:
                    word = int(word) ^ 65535

                self._state_word = list(word)[::-1]
                return True

    def _assemble_state_word(self, slot, channel, state):
        """
        convert bin array to an integer
        bin array stores msb at index 0
        so bin array needs to be reversed

        :param addr:
        :param state:
        :return:
        """
        if not self._state_word:
            self._read_state_word(slot)

        self._state_word[int(channel)] = int(state)
        return int(''.join(self._state_word[::-1]), 2)

    def _actuate(self, obj, action, excl=False):
        addr = get_switch_address(obj)
        slot = addr[0]
        state = action.lower() == 'open'

        word = self._assemble_state_word(slot, addr[1:], state)

        cmd = 'SOURCE:DIGITAL:DATA:WORD {},(@{}01)'.format(word, slot)
        self.tell(cmd)
        return self.get_channel_state(obj) is state
# ============= EOF =============================================
