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
from pychron.hardware.actuators.gp_actuator import GPActuator


class WiscArGPActuator(GPActuator):
    def get_state_checksum(self, keys):
        return 0

    def get_channel_state(self, obj, verbose=False, **kw):
        """
        """
        r = self.ask(obj.address)
        if r is None and globalv.communication_simulation:
            return True
        return r
        # cmd = '{}'.format(obj.address)
        #
        # s = self.ask(cmd, verbose=verbose)
        #
        # if s is not None:
        #     return s.strip() == 'True'

    def close_channel(self, obj):
        """
        """
        return self._actuate(False, obj)
        # cmd = '{}'.format(obj.address)
        #
        # r = self.ask(cmd)
        # if r is None and globalv.communication_simulation:
        #     return True
        #
        # if r is not None and r.strip() == 'OK':
        #     return self.get_channel_state(obj) is False

    def open_channel(self, obj):
        """
        """
        return self._actuate(True, obj)
        # cmd = 'Open {}'.format(obj.address)
        #
        # r = self.ask(cmd)
        # if r is None and globalv.communication_simulation:
        #     return True
        #
        # if r is not None and r.strip() == 'OK':
        #     return self.get_channel_state(obj) is True

    def _actuate(self, value, obj):
        r = self.ask((obj.address, value))
        if r is None and globalv.communication_simulation:
            return True

        if r is not None:
            return r.strip() == 'OK'
# ============= EOF =============================================
