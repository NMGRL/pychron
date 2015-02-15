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

# ============= enthought library imports =======================
from traits.api import List, Float, Bool
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import to_bool
from pychron.spectrometer.base_magnet import BaseMagnet, get_float
from pychron.spectrometer.thermo.spectrometer_device import SpectrometerDevice


class ArgusMagnet(BaseMagnet, SpectrometerDevice):
    """
    Magnet interface to Qtegra.

    uses MFTable object of mapping dac to mass
    """
    protected_detectors = List

    use_detector_protection = Bool
    use_beam_blank = Bool

    detector_protection_threshold = Float(0.1)  # DAC units
    beam_blank_threshold = Float(0.1)  # DAC units

    # ===============================================================================
    # ##positioning
    # ===============================================================================
    def set_dac(self, v, verbose=False):
        self.debug('setting dac {}'.format(v))
        micro = self.microcontroller
        unprotect = False
        unblank = False
        if micro:
            if self.use_detector_protection:
                if abs(self._dac - v) > self.detector_protection_threshold:
                    for pd in self.protected_detectors:
                        micro.ask('ProtectDetector {},On'.format(pd), verbose=verbose)
                    unprotect = True

            elif self.use_beam_blank:
                if abs(self._dac - v) > self.beam_blank_threshold:
                    micro.ask('BlankBeam True', verbose=verbose)
                    unblank = True

            micro.ask('SetMagnetDAC {}'.format(v), verbose=verbose)
            if not micro.simulation:
                time.sleep(self.settling_time)

            #only block if move is large and was made slowly.
            #this should be more explicit. get MAGNET_MOVE_THRESHOLD from RCS
            # and use it as to test whether to GetMagnetMoving
            if unprotect or unblank:
                for i in xrange(50):
                    if not to_bool(micro.ask('GetMagnetMoving')):
                        break
                    time.sleep(0.25)

                if unprotect:
                    for pd in self.protected_detectors:
                        micro.ask('ProtectDetector {},Off'.format(pd), verbose=verbose)
                if unblank:
                    micro.ask('BlankBeam False', verbose=verbose)

        change = v != self._dac
        if change:
            self._dac = v
            self.dac_changed = True
        return change

    @get_float
    def read_dac(self):
        if self.microcontroller is None:
            r = 0
        else:
            r = self.microcontroller.ask('GetMagnetDAC')
        return r

# ============= EOF =============================================
