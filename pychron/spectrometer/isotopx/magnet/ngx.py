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
from __future__ import absolute_import

from pychron.hardware import get_float
from pychron.spectrometer.isotopx.magnet.base import IsotopxMagnet


class NGXMagnet(IsotopxMagnet):
    def read_dac(self):
        return self.read_mass()

    def set_dac(self, v, *args, **kw):
        return self.set_mass(v, **kw)

    @get_float()
    def read_mass(self):
        # self.ask("StopAcq")
        self.microcontroller.stop_acquisition()
        # self.microcontroller.triggered = False
        return self.ask("GETMASS")

    def set_mass(self, v, delay=None, deflect=False, **kw):
        """

        :param v: mass
        :param delay: settling time in ms
        :param deflect:
        :return:
        """
        if delay is None:
            delay = int(self.settling_time * 1000)

        # self.ask("StopAcq")
        self.microcontroller.stop_acquisition()
        # self.microcontroller.triggered = False

        dv = abs(self._dac - v)
        self._dac = v

        if self.use_beam_blank:
            deflect = dv > self.beam_blank_threshold

        self.debug(
            f"use beam blank={deflect}. dv={dv}, threshold={self.beam_blank_threshold}"
        )

        deflect = ",deflect" if deflect else ""
        self.ask(f"SetMass {v},{delay}{deflect}")

        change = dv > 1e-7
        return change


# ============= EOF =============================================
