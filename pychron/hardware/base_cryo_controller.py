# ===============================================================================
# Copyright 2023 Jake Ross
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
import string
import time

from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice


class BaseCryoController(CoreDevice):
    def setpoints_achieved(self, setpoints, tol=1):
        pass

    def _block(self, setpoints, delay, block):
        if block:
            delay = max(0.5, delay)
            tol = 1
            if isinstance(block, (int, float)):
                tol = block

            while 1:
                if self.setpoints_achieved(setpoints, tol):
                    break
                time.sleep(delay)

    @get_float(default=0)
    def read_setpoint(self, output, verbose=False):
        return self._read_setpoint(output, verbose=verbose)

    @get_float(default=0)
    def read_input(self, v, **kw):
        if isinstance(v, int):
            v = string.ascii_lowercase[v - 1]
        return self._read_input(v, **kw)

    def set_setpoint(self, v, output=1, retries=3):
        sp = None
        for i in range(retries):
            self._write_setpoint(v, output)
            if not self.verify_setpoint:
                break
            sp = self.read_setpoint(output)
            if sp == v:
                break
        else:
            if self.verify_setpoint:
                self.warning_dialog(f"Failed setting setpoint to {v}. Got={sp}")

    def _write_setpoint(self, v, output):
        raise NotImplementedError

    def set_setpoints(self, *setpoints, block=False, delay=1):
        raise NotImplementedError

    def _read_setpoint(self, output, verbose=False):
        raise NotImplementedError

    def _read_input(self, v, **kw):
        raise NotImplementedError


# ============= EOF =============================================
