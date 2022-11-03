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

import time
from datetime import datetime

from traits.api import List

from pychron.hardware.nu_spectrometer_controller import NoblesseController
from pychron.pychron_constants import (
    NOBLESSE_DEFAULT_INTEGRATION_TIME,
    NOBLESSE_INTEGRATION_TIMES,
    NULL_STR,
    ATONA,
)
from pychron.spectrometer.base_spectrometer import BaseSpectrometer
# from pychron.spectrometer.nu import SOURCE_CONTROL_PARAMETERS, IsotopxMixin
from pychron.spectrometer.nu.detector.noblesse import NoblesseDetector
from pychron.spectrometer.nu.magnet.noblesse import NoblesseMagnet
from pychron.spectrometer.nu.source.noblesse import NoblesseSource
from pychron.core.codetools.inspection import caller


class NoblesseSpectrometer(BaseSpectrometer):
    # integration_time = Int
    integration_times = List(NOBLESSE_INTEGRATION_TIMES)

    magnet_klass = NoblesseMagnet
    detector_klass = NoblesseDetector
    source_klass = NoblesseSource
    microcontroller_klass = NoblesseController

    # rcs_id = "NOM"
    # username = Str('')
    # password = Str('')

    # _test_connect_command = "GETMASS"
    _read_enabled = True
    use_deflection_correction = False
    use_hv_correction = False
    # _triggered = False

    def _microcontroller_default(self):
        service = "pychron.hardware.nu_spectrometer_controller.NoblesseController"
        s = self.application.get_service(service)
        s.communicator.strip = False
        return s

    def make_configuration_dict(self):
        return {}

    def make_gains_dict(self):
        return {}

    def make_deflection_dict(self):
        return {}

    # def convert_to_axial(self, det, v):
    #     print("asdfsadf", det, det.index, v)
    #     v = v - (det.index - 2)
    #     return v

    # def start(self):
    #     self.set_integration_time(1, force=True)

    def finish_loading(self):
        super(NoblesseSpectrometer, self).finish_loading()
        config = self._get_cached_config()
        if config is not None:
            magnet = config["magnet"]
            # specparams, defl, trap, magnet = ret
            mftable_name = magnet.get("mftable")
            if mftable_name:
                self.debug("updating mftable name {}".format(mftable_name))
                self.magnet.field_table.path = mftable_name
                self.magnet.field_table.load_table(load_items=True)

    def _send_configuration(self, **kw):
        pass

    def _check_intensity_no_change(self, signals):
        return

    # def get_update_period(self, it=None, is_scan=False):
    #     """
    #     acquisition period is always set to 1s so update period always needs to be <1s
    #     """
    #
    #     if is_scan:
    #         return 0.1
    #
    #     return 0.95
    #     # return self.integration_time * 0.95

    # def trigger_acq(self, verbose=True):
    #     # self.debug('trigger acquie {}'.format(self.microcontroller.lock))
    #     # locking the microcontroller not necessary and detrimental when doing long integration times
    #     # other commands can be executed when waiting 10-20 sec integration period.
    #     # locking prevents those other command from happening. locking only ok when integration time < 5 seconds
    #     # probably (min time probably has to do with the update valve state frequency).
    #     # Disable locking complete for now
    #
    #     # another trick could be to make it an rlock. if lock is acquired by reading data then valve commands ok.
    #     # but not vis versa.
    #     # while self.microcontroller.lock.locked():
    #     #    time.sleep(0.25)
    #
    #     if not self.microcontroller.triggered:
    #         self.ask("StopAcq", verbose=verbose)
    #         self.microcontroller.triggered = True
    #         # return self.ask('StartAcq 1,{}'.format(self.rcs_id), verbose=verbose)
    #         return self.ask(
    #             "StartAcq {},{}".format(int(self.integration_time), self.rcs_id)
    #         )
    #     return True
    #
    # def readline(self, verbose=False):
    #     if verbose:
    #         self.debug("readline")
    #     st = time.time()
    #     ds = ""
    #     while 1:
    #         if time.time() - st > 3:  # (1.25 * self.integration_time):
    #             if verbose:
    #                 self.debug("readline timeout. raw={}".format(ds))
    #             return
    #
    #         if not self._read_enabled or self.microcontroller.canceled:
    #             self.microcontroller.canceled = False
    #             self.debug("readline canceled")
    #             return
    #
    #         try:
    #             ds += self.read(1)
    #         except BaseException:
    #             if not self.microcontroller.canceled:
    #                 self.debug_exception()
    #                 self.debug(f"data left: {ds}")
    #
    #         if "#\r\n" in ds:
    #
    #             ds = ds.split("#\r\n")[0]
    #             return ds

    def cancel(self):
        self.debug("canceling")
        self._read_enabled = False

    def read_intensities(
        self, timeout=60, trigger=False, target="ACQ.B", verbose=False
    ):
        self._read_enabled = True
        if verbose:
            self.debug(
                "read intensities trigger={} triggered={}".format(
                    trigger, self.microcontroller.triggered
                )
            )

        keys = []
        signals = []
        collection_time = None
        inc = False

        if len(signals) != len(keys):
            self.debug("keys={}".format(keys))
            self.debug("signals".format(signals))
            self.debug(
                "Number of signals {} and keys {} did not match".format(
                    len(signals), len(keys)
                )
            )
            keys, signals = [], []

        if verbose:
            self.debug("collection time: {}".format(collection_time))
            self.debug("keys: {}".format(keys))
            self.debug("signals: {}".format(signals))

        return keys, signals, collection_time, inc

    def read_integration_time(self):
        return self.integration_time

    def set_integration_time(self, it, force=False):
        """

        :param it: float, integration time in seconds
        :param force: set integration even if "it" is not different than self.integration_time
        :return: float, integration time
        """

        return it

    def read_parameter_word(self, keys):
        self.debug("read parameter word. keys={}".format(keys))
        values = []
        return values

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01]  # + random(6)
        keys = ["H2", "H1", "AX", "L1", "L2", "CDD"]
        return keys, signals, None

    def _integration_time_default(self):
        self.default_integration_time = NOBLESSE_DEFAULT_INTEGRATION_TIME
        return NOBLESSE_DEFAULT_INTEGRATION_TIME


# ============= EOF =============================================
