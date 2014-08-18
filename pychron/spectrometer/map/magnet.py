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

#============= enthought library imports =======================
from traits.api import Any
#============= standard library imports ========================
import time
#============= local library imports  ==========================
from pychron.spectrometer.base_magnet import BaseMagnet, get_float


class MapMagnet(BaseMagnet):
    device = Any

    #===============================================================================
    # ##positioning
    #===============================================================================
    def set_range(self, r, verbose=False):
        """
            r: float or int

            if float convert to integer and use as range
        """
        dev=self.device
        if dev:
            r = int(r) - 1
            dev.tell('B{}.'.format(r), verbose=verbose)

    def set_dac(self, v, verbose=False):
        dev=self.device
        if dev:
            self.set_range(v)
            dev.tell('W{}.'.format(v), verbose=verbose)
            time.sleep(self.settling_time)

        change = v != self._dac
        self._dac = v
        self.dac_changed = True
        return change

    @get_float
    def read_dac(self):
        return self.device.ask('') if self.device else 0

#============= EOF =============================================