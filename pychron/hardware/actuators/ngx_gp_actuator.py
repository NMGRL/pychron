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
    """ """

    open_cmd = "OpenValve"
    close_cmd = "CloseValve"
    affirmative = "E00"

    controller = None

    def ask(self, *args, **kw):
        if self.controller:
            return self.controller.ask(*args, **kw)

    def initialize(self, *args, **kw):
        service = "pychron.hardware.isotopx_spectrometer_controller.NGXController"
        s = self.application.get_service(service)
        if s is not None:
            self.controller = s
            # self._lock = self.controller.lock
            return True

    def actuate(self, *args, **kw):
        self.controller.set_acquisition_buffer(True)
        ret = super(NGXGPActuator, self).actuate(*args, **kw)
        self.controller.set_acquisition_buffer(False)
        return ret

    def get_channel_state(self, obj, delay=False, verbose=False, **kw):
        """ """
        if delay:
            if not isinstance(delay, (float, int)):
                delay = 0.25
        if delay:
            time.sleep(delay)

        # with self._lock:
        # self.debug(f'acquired lock {self._lock}')
        r = self._get_channel_state(obj, verbose=True, **kw)
        # self.debug(f'lock released')
        return r

    def _get_channel_state(self, obj, verbose=False, **kw):
        cmd = "GetValveStatus {}".format(get_switch_address(obj))
        s = self.ask(cmd, verbose=verbose)

        if s is not None:
            for si in s.split("\r\n"):
                if si.strip() == self.affirmative:
                    # time.sleep(0.2)
                    # recursively call get_channel_state
                    return self._get_channel_state(obj, verbose=verbose, **kw)
            for si in s.split("\r\n"):
                if si.strip() == "OPEN":
                    return True
            else:
                return False

        else:
            return False


# ============= EOF =====================================
