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
    acq_count = 0
    total_acq_count = 10
    has_atonas = True
    _last_collection_time = None
    _stale_event_count = 0
    _max_stale_event_count = 3
    # triggered_lock_release_required = False

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

    def protect_detector(self, pdets, protect):
        self.microcontroller.protect_detector = protect

    def convert_to_axial(self, det, v):
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

        self.has_atonas = any([d for d in self.detectors if d.kind in (ATONA, "CDD")])

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
            # self.microcontroller.lock.acquire()
            # self.triggered_lock_release_required = True

            # self.ask("StopAcq", verbose=verbose)
            self.microcontroller.stop_acquisition()
            self.microcontroller.begin_acquisition()
            self._reset_acquisition_progress()
            # return self.ask('StartAcq 1,{}'.format(self.rcs_id), verbose=verbose)
            self.total_acq_count = int(self.integration_time)
            return self.ask(
                "StartAcq {},{}".format(int(self.integration_time), self.rcs_id)
            )
        return True

    def readline(self, verbose=False, timeout=None):
        if verbose:
            self.debug("readline")
        st = time.time()
        ds = ""
        if timeout is None:
            timeout = self._get_read_timeout()
        while 1:
            if time.time() - st > timeout:
                if verbose:
                    self.debug("readline timeout. raw={}".format(ds))
                return

            if not self._read_enabled:
                # or self.microcontroller.canceled:
                # self.microcontroller.canceled = False
                self.debug("readline canceled")
                return

            try:
                # ds += self.read(1)
                # print(ds)
                ds = self.microcontroller.communicator.readline("#\r\n")
                # ds = self.microcontroller.communicator.select_read(terminator="#\r\n")
                # return ds
            except BaseException:
                if not self.microcontroller.canceled:
                    self.debug_exception()
                    self.debug(f"data left: {ds}")

            if ds and ds.endswith("#\r\n"):
                return ds[:-3]

            # if ds and "#\r\n" in ds:
            #     ds = ds.split("#\r\n")[0]
            #     return ds

    def cancel(self):
        self.debug("canceling")
        self._read_enabled = False
        if self.microcontroller:
            self.microcontroller.canceled = True

    def set_position_hook(self):
        self.debug("set position hook")
        self.microcontroller.stop_acquisition()

    def set_source_parameter(self, name, value):
        self.ask(f"SetSourceOutput {name},{value}")

    def read_intensities(self, timeout=60, trigger=False, target="ACQ.B", verbose=True):
        # self.microcontroller.lock.acquire()
        # verbose=True
        self._prepare_for_intensity_read()

        # verbose = True

        if verbose:
            self.debug(
                "read intensities trigger={} triggered={}".format(
                    trigger, self.microcontroller.triggered
                )
            )

        # self.microcontroller.lock.acquire()
        resp = True
        # trigger_release = self.triggered_lock_release_required
        # self.debug(f'trigger={trigger} triggered={self.microcontroller.triggered} '
        #            f'triggered_locrelease_required={self.triggered_lock_release_required}')
        # print('treigger', trigger, self.microcontroller.triggered)
        if self._should_trigger_acq(trigger):
            resp = self.trigger_acq()
            # trigger_release = self.microcontroller.triggered
            # self.debug(f'trigger_relase={trigger_release}')

            # self.microcontroller.lock.release()
            if resp is not None:
                time.sleep(self._get_trigger_wait())
        # else:
        # self.microcontroller.lock.acquire()
        # self.triggered_lock_release_required = True

        keys = []
        signals = []
        collection_time = None
        inc = False
        targeta, targetb = self._get_acquisition_targets()
        deadline = time.time() + self._get_intensity_deadline(timeout)
        if resp is not None:
            while self._read_enabled:
                # with self.microcontroller.lock:
                remaining = max(0.1, deadline - time.time())
                line = self.readline(verbose=verbose, timeout=remaining)

                if verbose:
                    self.debug("raw: {}".format(line))

                if line is None:
                    break

                parsed = self._parse_acquisition_event(line, targeta, targetb)
                if parsed is None:
                    continue

                collection_time = parsed["collection_time"]
                if self._is_stale_event(collection_time):
                    if self._handle_stale_event(collection_time):
                        break
                    continue

                signals, keys = self._filter_signals_for_event(
                    parsed["kind"], parsed["signals"]
                )
                if signals is None:
                    continue

                if parsed["kind"] == "ACQ":
                    self.acq_count += 1
                    if self.acq_count == self.total_acq_count and self.has_atonas:
                        # Ignore the terminal ACQ and wait for the buffered ACQ.B.
                        continue

                    if not self.has_atonas:
                        self._mark_acquisition_complete()
                        inc = True

                    break

                self._mark_acquisition_complete()
                inc = True
                break

            if not inc and self.microcontroller.triggered and time.time() >= deadline:
                self.warning("NGX acquisition timed out waiting for cycle completion")
                self._reset_incomplete_acquisition()

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

        # try:
        #     # the integration cycle is complete. release the lock
        #     if inc:
        #         self.microcontroller.lock.release()
        #         self.debug(f'Released lock. {self.microcontroller.lock}')
        # except RuntimeError as e:
        #     self.debug(f'Cannot release lock. "RuntimeError" {e}')

        # if self.triggered_lock_release_required:
        #     self.triggered_lock_release_required = False
        #     if trigger_release:
        # if self.microcontroller.lock.active_count() > 0:
        #     self.debug(f"trigger release. lock count={self.microcontroller.lock.count}")
        #     self.microcontroller.lock.release()
        # self.debug(f'trigger release. {trigger_release}')
        # if trigger_release:
        # self.triggered_lock_release_required = False

        # if self.microcontroller.lock.count>0:
        #     try:
        #         self.microcontroller.lock.release()
        #     except RuntimeError as e:
        #         if verbose:
        #             self.debug(f'Trigger Release. Cannot release lock. "RuntimeError" {e}')
        #     self.microcontroller.lock.release()
        # except RuntimeError as e:
        #     self.debug(f'Cannot release lock. "RuntimeError" {e}')
        #
        # if trigger_release:
        #     try:
        #         self.microcontroller.lock.release()
        #     except RuntimeError as e:
        #         self.debug(f'Trigger Release. Cannot release lock. "RuntimeError" {e}')

        return keys, signals, collection_time, inc

    def _prepare_for_intensity_read(self):
        self._read_enabled = True
        if self.microcontroller:
            self.microcontroller.clear_canceled()

    def _filter_signals_for_event(self, event_kind, signals):
        detectors = list(self.detectors[::-1])
        if len(signals) != len(detectors):
            self.warning(
                "NGX payload/detector count mismatch event={} signals={} detectors={}".format(
                    event_kind, len(signals), len(detectors)
                )
            )
            return None, None

        if self.has_atonas and event_kind == "ACQ":
            detectors = [d for d in detectors if d.kind in ("CDD", ATONA)]
            signals = [
                signal
                for signal, det in zip(signals, self.detectors[::-1])
                if det.kind in ("CDD", ATONA)
            ]
        else:
            signals = list(signals)

        return signals, [det.name for det in detectors]

    def _get_acquisition_targets(self):
        return (
            "#EVENT:ACQ,{}".format(self.rcs_id),
            "#EVENT:ACQ.B,{}".format(self.rcs_id),
        )

    def _get_intensity_deadline(self, timeout):
        return min(timeout, self._get_read_timeout() * 2)

    def _get_read_timeout(self):
        return max(3.0, self.integration_time * 1.5 + 2.0)

    def _get_trigger_wait(self):
        return min(0.95, max(0.05, self.integration_time * 0.2))

    def _parse_acquisition_event(self, line, targeta, targetb):
        if not line:
            return

        if line.startswith(targeta):
            kind = "ACQ"
        elif line.startswith(targetb):
            kind = "ACQ.B"
        else:
            return

        args = line.split(",")
        if len(args) < 6:
            self.warning("Malformed NGX event payload: {}".format(line))
            return

        try:
            cd = datetime.today()
            ct = datetime.strptime(args[4], "%H:%M:%S.%f").time()
            collection_time = datetime.combine(cd, ct)
        except (TypeError, ValueError) as e:
            self.warning("Invalid NGX event timestamp line={} error={}".format(line, e))
            return

        try:
            signals = [float(i.strip()) for i in args[5:]]
        except ValueError as e:
            self.warning("Invalid NGX event signal payload line={} error={}".format(line, e))
            return

        return {
            "kind": kind,
            "collection_time": collection_time,
            "signals": signals,
        }

    def _should_trigger_acq(self, trigger):
        return trigger or not self.microcontroller.triggered

    def _reset_acquisition_progress(self):
        self.acq_count = 0
        self._stale_event_count = 0
        self._last_collection_time = None

    def _mark_acquisition_complete(self):
        self.acq_count = 0
        self._stale_event_count = 0
        if self.microcontroller:
            self.microcontroller.triggered = False

    def _reset_incomplete_acquisition(self):
        self._reset_acquisition_progress()
        if self.microcontroller and self.microcontroller.triggered:
            self.microcontroller.stop_acquisition()

    def _is_stale_event(self, collection_time):
        if collection_time is None:
            return False

        last = self._last_collection_time
        self._last_collection_time = collection_time
        return last is not None and collection_time <= last

    def _handle_stale_event(self, collection_time):
        self._stale_event_count += 1
        self.warning(
            "Ignoring stale NGX acquisition event time={} count={}".format(
                collection_time, self._stale_event_count
            )
        )
        if self._stale_event_count >= self._max_stale_event_count:
            self.warning("Resetting NGX acquisition after repeated stale events")
            self._reset_incomplete_acquisition()
            return True

        return False

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
        # self.ask("StopAcq")
        self.microcontroller.stop_acquisition()
        self.ask("SetAcqPeriod 1000")
        self._read_enabled = False
        self._reset_acquisition_progress()
        # self.microcontroller.triggered = False
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
