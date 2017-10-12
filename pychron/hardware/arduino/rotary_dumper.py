# ===============================================================================
# Copyright 2017 ross
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
from pychron.hardware.core.headless.core_device import HeadlessCoreDevice

MAGNET = 0
MOVE = 1
RPM = 2
STATUS = 3
RELEASE = 4
OK = 5
ERROR = 6


class RotaryDumper(HeadlessCoreDevice):
    _nsteps = 0

    def energize(self, nsteps, rpm=None):
        if rpm:
            self.ask('{},{};'.format(RPM, rpm))

        self.ask('{},1;'.format(MAGNET))
        self.ask('{},{};'.format(MOVE, nsteps))
        self._nsteps = nsteps

    def denergize(self, nsteps=None):
        if nsteps is None:
            nsteps = -self._nsteps

        if nsteps > 0:
            nsteps = -nsteps

        self.ask('{},0;'.format(MAGNET))
        self.ask('{},{};'.format(MOVE, nsteps))

    def is_energized(self):
        """
          /* return status as a integer
   *  Bit 0 =  mode 0==software 1 manual
   *      1 =  moving 0 stop 1 in motion
   *      2 =  magnet 0 off 1 on
   */
        @return:
        """
        state = self.ask('{};'.format(STATUS))
        return int(state) >= 6

    def _get_dump_state(self):
        return self.is_energized()

# ============= EOF =============================================
