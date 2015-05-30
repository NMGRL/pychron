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

#========== standard library imports ==========

#========== local library imports =============
from gp_actuator import GPActuator


class QtegraGPActuator(GPActuator):
    """

    """

#    def initialize(self, *args, **kw):
#        '''
#            @type *args: C{str}
#            @param *args:
#
#            @type **kw: C{str}
#            @param **kw:
#        '''
#        self._communicator._terminator = chr(10)

    def get_channel_state(self, obj, verbose=False):
        """
        """

        # returns one if channel close  0 for open
#        if isinstance(obj, (str, int)):
#            addr = obj
#        else:
#            addr = obj.address

        cmd = 'GetValveState {}'.format(obj.address)

        s = self.ask(cmd, verbose=verbose)

        if s is not None:
            if s.strip() in 'True':
                return True
            else:
                return False
        else:
            return False

    def close_channel(self, obj):
        """
        """

        cmd = 'Close {}'.format(obj.address)

        r = self.ask(cmd)
        if r is not None and r.strip() == 'OK':
            return self.get_channel_state(obj) == False

    def open_channel(self, obj):
        """
        """
        print 'asdfasdf'
        cmd = 'Open {}'.format(obj.address)

        r = self.ask(cmd)
        if r is not None and r.strip() == 'OK':
            return self.get_channel_state(obj) == True
# ============= EOF =====================================
