#===============================================================================
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
#===============================================================================

#========== standard library imports ==========

#========== local library imports =============
from pychron.hardware.actuators.gp_actuator import GPActuator


class AgilentGPActuator(GPActuator):
    """
        Abstract module for the Agilent 34903A GP AgilentGPActuator

    """
    id_query = '*TST?'

    def id_response(self, response):
        if response.strip() == '0':
            return True

    def initialize(self, *args, **kw):
        """
        """
        self.debug('initializing')

        self.debug('setting write_terminator to chr(10)')
        self._communicator.write_terminator = chr(10)

        # clear and record any accumulated errors
        errs = self._get_errors()
        if errs:
            self.warning('\n'.join(errs))
        return True

    def get_channel_state(self, obj):
        """
            Query the hardware for the channel state
        """

        # returns one if channel close  0 for open
        cmd = 'ROUT:OPEN? (@{})'.format(self._get_address(obj))
        s = self.ask(cmd)
        if self.simulation:
            return

        if s is not None:
            return s[:1] == '1'

    def close_channel(self, obj, excl=False):
        """
            Close the channel
        """

        address = self._get_address(obj)
        if not excl:
            cmd = 'ROUT:CLOSE (@{})'.format(address)
        else:
            # ensure all channels open before closing
            cmd = 'ROUT:CLOS:EXCL (@{})'.format(address)
        self.tell(cmd)
        if self.simulation:
            return True
        return self.get_channel_state(obj) == False

    def open_channel(self, obj):
        """
            open the channel
        """

        cmd = 'ROUT:OPEN (@{})'.format(self._get_address(obj))
        self.tell(cmd)
        if self.simulation:
            return True
        return self.get_channel_state(obj) == True

    def _get_errors(self):
        # maximum of 10 errors so no reason to use a while loop
        def gen_error():
            for _i in xrange(10):
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
                if s != '+0,"No error"':
                    error = s

        return error

    def _get_address(self, obj):
        if isinstance(obj, (str, int)):
            addr = obj
        else:
            addr = obj.address
        return addr


#============= EOF =====================================
