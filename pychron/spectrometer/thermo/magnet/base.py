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
from __future__ import absolute_import
import time

from traits.api import List, Float, Bool

from pychron.core.helpers.strtools import to_bool
from pychron.globals import globalv
from pychron.hardware import get_float
from pychron.spectrometer.base_magnet import BaseMagnet
from six.moves import range


class ThermoMagnet(BaseMagnet):
    """
    Magnet interface to Qtegra.

    uses MFTable object of mapping dac to mass
    """

    protected_detectors = List

    use_detector_protection = Bool
    use_beam_blank = Bool

    # detector_protection_threshold = Float(0.1)  # DAC units
    beam_blank_threshold = Float(0.1)  # DAC units

    # ===============================================================================
    # ##positioning
    # ===============================================================================
    def set_dac(
        self,
        v,
        verbose=True,
        settling_time=None,
        use_dac_changed=True,
        use_af_demag=True,
    ):
        # if not self._wait_lock(2):
        #     self.debug('Unabled to obtain set_dac lock. Another thread is moving the magnet')
        #     return
        if verbose:
            self.debug("setting magnet DAC")
            self.debug("current  : {:0.6f}".format(self._dac))
            self.debug("requested: {:0.6f}".format(v))

        dv = abs(self._dac - v)
        if verbose:
            self.debug("Delta Dac: {:0.6f}".format(dv))

        unprotect = []
        unblank = False

        if self.use_detector_protection:
            if verbose:
                self.debug("Checking detector protection. dv={:0.5f}".format(dv))
            for pd in self.protected_detectors:
                det = self.spectrometer.get_detector(pd)
                if verbose:
                    self.debug(
                        'Checking detector "{}". '
                        "Protection Threshold: {} (V)".format(
                            pd, det.protection_threshold
                        )
                    )
                if det is None:
                    self.warning("Invalid detector to protect: {}".format(pd))
                    continue
                if det.protection_threshold and dv > det.protection_threshold:
                    self.ask("ProtectDetector {},On".format(pd), verbose=verbose)
                    resp = self.ask("GetDeflection {}".format(pd), verbose=verbose)
                    unprotect.append(pd)
                    if verbose:
                        self.debug("Protected = {}".format(resp))

        if self.use_beam_blank:
            if dv > self.beam_blank_threshold:
                self.ask("BlankBeam True", verbose=verbose)
                unblank = True

        if self.use_af_demagnetization and use_af_demag:
            if dv > self.af_demag_threshold or use_af_demag == "force":
                if verbose:
                    self.debug(
                        "Do AF Demag. UseAFDemag={}, "
                        "delta_volts={}, threshold={}".format(
                            use_af_demag, dv, self.af_demag_threshold
                        )
                    )
                self.ask("BlankBeam True", verbose=verbose)
                unblank = True
                self._do_af_demagnetization(
                    v, lambda dd: self.ask("SetMagnetDAC {}".format(dd))
                )
        else:
            if verbose:
                self.debug(
                    "AF Demag not enabled. "
                    "self.use_af_demag={}, use_af_demag={}".format(
                        self.use_af_demagnetization, use_af_demag
                    )
                )
        self.ask("SetMagnetDAC {}".format(v), verbose=verbose)

        change = dv > 1e-7
        if change:
            if settling_time is None:
                settling_time = self.settling_time
            if verbose:
                self.debug(
                    "Magnet settling time: {:0.3f} {:0.3f}".format(
                        settling_time, self.settling_time
                    )
                )
            if settling_time > 0:
                time.sleep(settling_time)
                if verbose:
                    self.debug("Magnet settling complete")

            if unprotect or unblank:
                if verbose:
                    self.debug("Wait for magnet to stop moving")
                for i in range(50):
                    if not to_bool(self.ask("GetMagnetMoving", verbose=verbose)):
                        break
                    time.sleep(0.25)
                if verbose:
                    self.debug("Magnet move complete")

                if unprotect:
                    if verbose:
                        self.debug("Unprotect detectors")
                    for d in unprotect:
                        self.ask("ProtectDetector {},Off".format(d), verbose=verbose)
                        self.ask("GetDeflection {}".format(d), verbose=verbose)

                if unblank:
                    if verbose:
                        self.debug("Unblank beam")
                    self.ask("BlankBeam False", verbose=verbose)

        self._dac = v

        if globalv.experiment_debug:
            change = True

        if verbose:
            self.debug("set_dac. change={}".format(change))
        # self._wait_release()
        if use_dac_changed and change:
            self.dac_changed = True

        return change

    @get_float(default=0)
    def read_dac(self):
        return self.ask("GetMagnetDAC")


# ============= EOF =============================================
