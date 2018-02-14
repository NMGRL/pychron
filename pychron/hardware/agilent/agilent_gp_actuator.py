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
from pychron.hardware.actuators.gp_actuator import GPActuator
from six.moves import range


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
        errs = self._get_errors()
        if errs:
            self.warning('\n'.join(errs))
        return True

    def get_channel_state(self, obj, verbose=False, **Kw):
        """
            Query the hardware for the channel state
        """

        # returns one if channel close  0 for open
        cmd = 'ROUT:{}? (@{})'.format(self._get_cmd('OPEN'), self._get_address(obj))
        s = self.ask(cmd, verbose=verbose)
        if self.simulation:
            return

        if s is not None:
            return s[:1] == '1'

    def close_channel(self, obj, excl=False):
        """
            Close the channel
        """

        address = self._get_address(obj)
        cmd = self._get_cmd('CLOSE')
        if not excl:
            cmd = 'ROUT:{} (@{})'.format(cmd, address)
        else:
            # ensure all channels open before closing
            cmd = 'ROUT:{}:EXCL (@{})'.format(cmd, address)
        self.tell(cmd)
        if self.simulation:
            return True
        return self.get_channel_state(obj) == False

    def open_channel(self, obj):
        """
            open the channel
        """

        cmd = 'ROUT:{} (@{})'.format(self._get_cmd('OPEN'), self._get_address(obj))
        self.tell(cmd)
        if self.simulation:
            return True
        return self.get_channel_state(obj) == True

    # private
    def _get_cmd(self, cmd):
        if self.invert:
            cmd = 'CLOSE' if cmd == 'OPEN' else 'OPEN'
        return cmd

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
        self.debug('get error. simulation:{}'.format(self.simulation))
        error = None
        cmd = 'SYST:ERR?'
        if not self.simulation:
            s = self.ask(cmd)
            if s is not None:
                s = s.strip()
                if s != '+0,"No error"':
                    error = s

        return error

    def _get_address(self, obj):
        if isinstance(obj, (str, int)):
            addr = obj
        else:
            addr = obj.address
        return addr

# ============= EOF =====================================
