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
from __future__ import print_function

import time
from datetime import datetime

from traits.api import List

from pychron.hardware.isotopx_spectrometer_controller import NGXController
from pychron.pychron_constants import (
    ISOTOPX_DEFAULT_INTEGRATION_TIME,
    ISOTOPX_INTEGRATION_TIMES,
    NULL_STR,
    ATONA,
)
from pychron.spectrometer.base_spectrometer import BaseSpectrometer
from pychron.spectrometer.isotopx import SOURCE_CONTROL_PARAMETERS, IsotopxMixin
from pychron.spectrometer.isotopx.detector.ngx import NGXDetector
from pychron.spectrometer.isotopx.magnet.ngx import NGXMagnet
from pychron.spectrometer.isotopx.source.ngx import NGXSource
from pychron.core.codetools.inspection import caller


class NGXSpectrometer(BaseSpectrometer, IsotopxMixin):
    # integration_time = Int
    integration_times = List(ISOTOPX_INTEGRATION_TIMES)

    magnet_klass = NGXMagnet
    detector_klass = NGXDetector
    source_klass = NGXSource
    microcontroller_klass = NGXController

    rcs_id = "NOM"
    # username = Str('')
    # password = Str('')

    _test_connect_command = "GETMASS"
    _read_enabled = True
    use_deflection_correction = False
    use_hv_correction = False
    _triggered = False
    acq_count = None
    total_acq_count = 10

    def _microcontroller_default(self):
        service = "pychron.hardware.isotopx_spectrometer_controller.NGXController"
        s = self.application.get_service(service)
        s.communicator.strip = False
        return s

    def make_configuration_dict(self):
        return {}

    def make_gains_dict(self):
        return {}

    def make_deflection_dict(self):
        return {}

    def convert_to_axial(self, det, v):
        print("asdfsadf", det, det.index, v)
        v = v - (det.index - 2)
        return v

    def start(self):
        self.set_integration_time(1, force=True)

    def finish_loading(self):
        super(NGXSpectrometer, self).finish_loading()
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

    def get_update_period(self, it=None, is_scan=False):
        """
        acquisition period is always set to 1s so update period always needs to be <1s
        """

        if is_scan:
            return 0.1

        return 0.95
        # return self.integration_time * 0.95

    def trigger_acq(self, verbose=True):
        # self.debug('trigger acquie {}'.format(self.microcontroller.lock))
        # locking the microcontroller not necessary and detrimental when doing long integration times
        # other commands can be executed when waiting 10-20 sec integration period.
        # locking prevents those other command from happening. locking only ok when integration time < 5 seconds
        # probably (min time probably has to do with the update valve state frequency).
        # Disable locking complete for now

        # another trick could be to make it an rlock. if lock is acquired by reading data then valve commands ok.
        # but not vis versa.
        # while self.microcontroller.lock.locked():
        #    time.sleep(0.25)

        if not self.microcontroller.triggered:
            self.ask("StopAcq", verbose=verbose)
            self.microcontroller.triggered = True
            # return self.ask('StartAcq 1,{}'.format(self.rcs_id), verbose=verbose)
            self.total_acq_count = int(self.integration_time)
            return self.ask(
                "StartAcq {},{}".format(int(self.integration_time), self.rcs_id)
            )
        return True

    def readline(self, verbose=False):
        if verbose:
            self.debug("readline")
        st = time.time()
        ds = ""
        while 1:
            if time.time() - st > 3:  # (1.25 * self.integration_time):
                if verbose:
                    self.debug("readline timeout. raw={}".format(ds))
                return

            if not self._read_enabled or self.microcontroller.canceled:
                self.microcontroller.canceled = False
                self.debug("readline canceled")
                return

            try:
                ds += self.read(1)
            except BaseException:
                if not self.microcontroller.canceled:
                    self.debug_exception()
                    self.debug(f"data left: {ds}")

            #            if "#\r\n" in ds:
            #                ds = ds.split("#\r\n")[0]

            if "#" in ds:
                ds = ds.split("#")[0]
                return ds

    def cancel(self):
        self.debug("canceling")
        self._read_enabled = False

    def read_intensities(
        self, timeout=60, trigger=False, target="ACQ.B", verbose=False
    ):
        # self.microcontroller.lock.acquire()
        # verbose=True
        self._read_enabled = True

        verbose = True

        if verbose:
            self.debug(
                "read intensities trigger={} triggered={}".format(
                    trigger, self.microcontroller.triggered
                )
            )
        resp = True
        if trigger:
            resp = self.trigger_acq()
            # self.microcontroller.lock.release()
            if resp is not None:
                # if verbose:
                #     self.debug(f'waiting {self.integration_time * 0.95} before trying to get data')
                # time.sleep(self.integration_time * 0.95)
                time.sleep(0.95)
                # if verbose:
                #     self.debug('trigger wait finished')

        keys = []
        signals = []
        collection_time = None
        inc = False
        # self.debug(f'acquired mcir lock {self.microcontroller.lock}')
        targetb = "EVENT:ACQ.B,{}".format(self.rcs_id)
        targeta = "EVENT:ACQ,{}".format(self.rcs_id)
        if resp is not None:
            keys = self.detector_names[::-1]
            while self._read_enabled:
                with self.microcontroller.lock:
                    line = self.readline(verbose=True)

                if verbose:
                    self.debug("raw: {}".format(line))

                if line is None:
                    break

                if line and (line.startswith(targeta) or line.startswith(targetb)):
                    try:
                        args = line.split(",")

                        cd = datetime.today()
                        ct = datetime.strptime(args[4], "%H:%M:%S.%f").time()

                        collection_time = datetime.combine(cd, ct)
                        signals = [float(i.strip()) for i in args[5:]]
                        print("fad", keys, signals)
                        if line.startswith(targeta):
                            self.acq_count += 1
                            if self.acq_count == self.total_acq_count:
                                # forget this ACQ and immediately get the ACQ.B record.
                                continue
                            else:
                                nsignals, keys = [], []
                                for i, di in enumerate(self.detectors[::-1]):
                                    if di.kind == "CDD":
                                        nsignals.append(signals[i])
                                        keys.append(di.name)
                                signals = nsignals
                                break

                        elif line.startswith(targetb):
                            self.acq_count = 0
                            self.microcontroller.triggered = False
                            inc = True

                            break
                    except BaseException as e:
                        self.debug("read intensities errror={}".format(e))

        # self.microcontroller.lock.release()
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
        self.debug(
            "acquisition period set to 1 second.  integration time set to {}".format(it)
        )
        self.ask("StopAcq")
        self.ask("SetAcqPeriod 1000")
        self._read_enabled = False
        self.microcontroller.triggered = False
        self.integration_time = it

        # if self.integration_time != it or force:
        #     self.ask('StopAcq')
        #     self.debug('setting integration time = {}'.format(it))
        #
        #     self.ask('SetAcqPeriod {}'.format(int(it * 1000)))
        #     self.trait_setq(integration_time=it)

        return it

    def read_parameter_word(self, keys):
        self.debug("read parameter word. keys={}".format(keys))
        values = []
        for kk in keys:
            try:
                key = SOURCE_CONTROL_PARAMETERS[kk]
            except KeyError:
                values.append(NULL_STR)
                continue

            resp = self.ask("GetSourceOutput {}".format(key))
            if resp is not None:
                try:
                    last_set, readback = resp.split(",")
                    values.append(float(readback))
                except ValueError:
                    values.append(NULL_STR)
        return values

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01]  # + random(6)
        keys = ["H2", "H1", "AX", "L1", "L2", "CDD"]
        return keys, signals, None

    def _integration_time_default(self):
        self.default_integration_time = ISOTOPX_DEFAULT_INTEGRATION_TIME
        return ISOTOPX_DEFAULT_INTEGRATION_TIME


# ============= EOF =============================================
