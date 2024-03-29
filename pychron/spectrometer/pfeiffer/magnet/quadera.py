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
from pychron.spectrometer.pfeiffer.magnet.base import PfeifferMagnet


class QuaderaMagnet(PfeifferMagnet):
    def read_dac(self):
        return self.read_mass()

    def set_dac(self, v, *args, **kw):
        return self.set_mass(v)

    @get_float()
    def read_mass(self):
        self.ask("StopAcq")
        return self.ask("GETMASS")

    def set_mass(self, v, delay=None, deflect=False):
        """

        :param v: mass
        :param delay: settling time in ms
        :param deflect:
        :return:
        """
        if delay is None:
            delay = int(self.settling_time * 1000)

        self.ask("StopAcq")
        deflect = ",deflect" if deflect else ""
        self.ask("SetMass {},{}{}".format(v, delay, deflect))

        dv = abs(self._dac - v)
        self._dac = v
        change = dv > 1e-7

        return change


# ============= EOF =============================================
