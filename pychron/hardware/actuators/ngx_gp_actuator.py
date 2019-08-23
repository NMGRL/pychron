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
# =============================================== ================================

# ========== standard library imports ==========
import time

# ========== local library imports =============
from pychron.hardware.actuators import get_switch_address
from pychron.hardware.actuators.ascii_gp_actuator import ASCIIGPActuator


class NGXGPActuator(ASCIIGPActuator):
    """

    """
    _open_cmd = 'OpenValve'
    _close_cmd = 'CloseValve'
    _affirmative = 'E00'

    def initialize(self, *args, **kw):
        service = 'pychron.hardware.isotopx_spectrometer_controller.NGXController'
        s = self.application.get_service(service)
        if s is not None:
            self.communicator = s.communicator
            return True

    def get_channel_state(self, obj, delay=False, verbose=True, **kw):
        """
        """
        if delay:
            if not isinstance(delay, (float, int)):
                delay = 0.25
            time.sleep(delay)

        cmd = 'GetValveStatus {}'.format(get_switch_address(obj))

        s = self.ask(cmd, verbose=verbose)
        if s is not None:
            if s.strip() == 'E00':
                time.sleep(0.25)
                # recusively call get_channel_state
                return self.get_channel_state(obj, verbose=verbose, **kw)

            return s.strip() == 'OPEN'

        else:
            return False

# ============= EOF =====================================
