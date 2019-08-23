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
from __future__ import absolute_import

from six.moves import range

from pychron.hardware.actuators import get_switch_address, get_valve_name
from pychron.hardware.actuators.gp_actuator import GPActuator


class AgilentGPActuator(GPActuator):
    """
        Abstract module for the Agilent 34903A GP AgilentGPActuator

    """
    id_query = '*TST?'
    invert = False

    def id_response(self, response):
        if response.strip() == '0':
            return True

    def load_additional_args(self, config, **kw):
        self.set_attribute(config, 'invert', 'General', 'invert')
        return True

    def initialize(self, *args, **kw):
        """
        """
        self.debug('initializing')

        self.debug('setting write_terminator to chr(10)')
        self.communicator.write_terminator = chr(10)

        # clear and record any accumulated errors
        self._clear_and_report_errors()
        return True

    def get_channel_state(self, obj, verbose=False, **kw):
        """
            Query the hardware for the channel state
        """

        # returns one if channel close  0 for open
        cmd = 'ROUT:{}? (@{})'.format(self._get_cmd('OPEN'), get_switch_address(obj))
        s = self.ask(cmd, verbose=verbose)
        if self.simulation:
            return

        if s is not None:
            return s[:1] == '1'

    def close_channel(self, obj, excl=False):
        """
            Close the channel
        """

        return self._actuate(obj, 'CLOSE', excl)

    def open_channel(self, obj):
        """
            Open the channel
        """
        return self._actuate(obj, 'OPEN')

    def _actuate(self, obj, action, excl=False):
        state = action == 'OPEN'
        addr = get_switch_address(obj)
        if not addr:
            name = get_valve_name(obj)
            self.warning_dialog('Address not set for valve "{}"'.format(name))

        cmd = 'ROUT:{}{} (@{})'.format(self._get_cmd(action), ':EXCL' if excl else '', addr)
        self.tell(cmd)
        if self.simulation:
            return True
        return self.get_channel_state(obj) is state

    # private
    def _get_cmd(self, cmd):
        if self.invert:
            cmd = 'CLOSE' if cmd == 'OPEN' else 'OPEN'
        return cmd

    def _clear_and_report_errors(self):
        self.info('Clear and Report Errors. simulation:{}'.format(self.simulation))

        es = self._get_errors()
        self.info('------------------------ Errors ------------------------')
        if es:
            for ei in es:
                self.warning(ei)
        else:
            self.info('No Errors')
        self.info('--------------------------------------------------------')

    def _get_errors(self):
        # maximum of 10 errors so no reason to use a while loop
        def gen_error():
            for _i in range(10):
                error = self._get_error()
                if error is None:
                    break
                else:
                    yield error

        return list(gen_error())

    def _get_error(self):
        error = None
        cmd = 'SYST:ERR?'
        if not self.simulation:
            s = self.ask(cmd)
            if s is not None:
                s = s.strip()
                if s != '+0,"No error"':
                    error = s

        return error

# ============= EOF =====================================
