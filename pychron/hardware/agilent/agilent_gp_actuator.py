# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ========== standard library imports ==========

# ========== local library imports =============
from pychron.hardware.actuators import get_switch_address, get_valve_name
from pychron.hardware.actuators.gp_actuator import GPActuator
from pychron.hardware.agilent.agilent_mixin import AgilentMixin


class AgilentGPActuator(AgilentMixin, GPActuator):
    """
    :::
    name: Agilent 34903A
    description: Abstract module for the Agilent 34903A GP AgilentGPActuator
    website: https://www.keysight.com/us/en/product/34903A/20-channel-actuator-gp-switch-module.html
    """

    # def get_indicator_state(self, obj, *args, **kw):
    #     """
    #     state word is a list of 16 bits
    #     return True if read properly
    #
    #     :return:
    #     """
    #     # if port not in (1, 2):
    #     #     self.warning("Invalid port number {}. defaulting to port 1".format(port))
    #     #     port = 1
    #
    #     #base = "SENS:DIG:DATA:{}? (@{}{:02n})"
    #     datatype = "BYTE"
    #     #datatype = "WORD"
    #     # if as_word:
    #     #     datatype = "WORD"
    #     #     port = 1
    #     addr = get_switch_address(obj)
    #     cmd = "SENS:DIG:DATA:{}? (@{})".format(datatype, addr)
    #     resp = self.ask(cmd, verbose=True)
    #     if resp:
    #         resp = resp.strip()
    #         if resp:
    #             nbits = 16
    #             fmt = "{{:0{}b}}".format(nbits)
    #
    #             resp = resp.split(",")[0]
    #             word = fmt.format(int(float(resp)))
    #             if self.invert:
    #                 word = fmt.format(int(word, 2) ^ (2 ** nbits - 1))
    #
    #             print('asdf', word)
    #             #self._state_word = list(word)[::-1]
    #             return True
    # def get_indicator_state(self, obj, *args, **kw):

    #   return self.get_channel_state(obj)

    def get_channel_state(self, obj, verbose=True, **kw):
        """
        Query the hardware for the channel state
        """

        # returns one if channel close  0 for open
        cmd = "ROUT:{}? (@{})".format(self._get_cmd("OPEN"), get_switch_address(obj))
        s = self.ask(cmd, verbose=verbose)
        if self.simulation:
            return

        if s:
            return s[0] == "1"

    def close_channel(self, obj, excl=False):
        """
        Close the channel
        """

        return self._actuate(obj, "CLOSE", excl)

    def open_channel(self, obj):
        """
        Open the channel
        """
        return self._actuate(obj, "OPEN")

    def _actuate(self, obj, action, excl=False):
        state = action == "OPEN"
        addr = get_switch_address(obj)
        if not addr:
            name = get_valve_name(obj)
            self.warning_dialog('Address not set for valve "{}"'.format(name))

        cmd = "ROUT:{}{} (@{})".format(
            self._get_cmd(action), ":EXCL" if excl else "", addr
        )
        self.tell(cmd)
        if self.simulation:
            return True
        self._clear_and_report_errors()
        return self.get_channel_state(obj) is state

    # private
    def _get_cmd(self, cmd):
        if self.invert:
            cmd = "CLOSE" if cmd == "OPEN" else "OPEN"
        return cmd


# ============= EOF =====================================
