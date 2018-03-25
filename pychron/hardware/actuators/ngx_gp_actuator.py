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
from pychron.globals import globalv


class NGXGPActuator(GPActuator):
    """

    """

    def initialize(self, *args, **kw):
        service = 'pychron.hardware.isotopx_spectrometer_controller.NGXController'
        s = self.application.get_service(service)
        if s is not None:
            self.communicator = s.communicator
            return True

    def get_state_checksum(self, keys):
        return 0

    def get_channel_state(self, obj, delay=False, verbose=True, **kw):
        """
        """
        if delay:
            if not isinstance(delay, (float, int)):
                delay = 0.25
            time.sleep(delay)

        cmd = 'GetValveStatus {}'.format(obj.address)

        s = self.ask(cmd, verbose=verbose)
        if s is not None:
            if s.strip() == 'E00':
                time.sleep(0.25)
                # recusively call get_channel_state
                return self.get_channel_state(obj, verbose=verbose, **kw)

            return s.strip() == 'OPEN'

        else:
            return False

    def close_channel(self, obj):
        """
        """

        cmd = 'CloseValve {}'.format(obj.address)

        r = self.ask(cmd)
        if r is None and globalv.communication_simulation:
            return True

        if r is not None and r.strip() == 'E00':
            return self.get_channel_state(obj, delay=True) is False

    def open_channel(self, obj):
        """
        """
        cmd = 'OpenValve {}'.format(obj.address)

        r = self.ask(cmd)
        if r is None and globalv.communication_simulation:
            return True

        if r is not None and r.strip() == 'E00':
            return self.get_channel_state(obj, delay=True) is True

# ============= EOF =====================================
