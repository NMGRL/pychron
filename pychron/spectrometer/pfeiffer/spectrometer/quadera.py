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
import json
import struct
import time
from datetime import datetime
from numpy import append as npappend

from traits.api import List

from pychron.hardware.quadera_spectrometer_controller import QuaderaController

from pychron.processing.isotope import Isotope
from pychron.processing.isotope_group import IsotopeGroup
from pychron.pychron_constants import (
    ISOTOPX_DEFAULT_INTEGRATION_TIME,
    ISOTOPX_INTEGRATION_TIMES,
    NULL_STR,
    QUADERA_DEFAULT_INTEGRATION_TIME,
    QUADERA_INTEGRATION_TIMES,
)

from pychron.spectrometer.base_spectrometer import BaseSpectrometer

# from pychron.spectrometer.isotopx import SOURCE_CONTROL_PARAMETERS, IsotopxMixin

from pychron.spectrometer.pfeiffer import PfeifferMixin
from pychron.spectrometer.pfeiffer.detector.quadera import QuaderaDetector
from pychron.spectrometer.pfeiffer.magnet.quadera import QuaderaMagnet
from pychron.spectrometer.pfeiffer.source.quadera import QuaderaSource


class QuaderaSpectrometer(BaseSpectrometer, PfeifferMixin):
    # integration_time = Int
    integration_times = List(QUADERA_INTEGRATION_TIMES)

    magnet_klass = QuaderaMagnet
    detector_klass = QuaderaDetector
    source_klass = QuaderaSource
    microcontroller_klass = QuaderaController

    # _test_connect_command = 'GETMASS'
    # _read_enabled = True
    use_deflection_correction = False
    use_hv_correction = False

    def _microcontroller_default(self):
        # service = 'pychron.hardware.quadera_spectrometer_controller.QuaderaController'
        # s = self.application.get_service(service)

        s = QuaderaController(name="spectrometer_microcontroller")
        s.bootstrap()
        s.communicator.simulation = True
        return s

    def set_data_pump_mode(self, mode):
        pass

    def sink_data(self, writer, n, delay):

        client = self.microcontroller.communicator
        handle = client.get_handler()
        sock = handle.sock
        # get the data
        header = None
        cnt = 1
        start_time = st = time.time()
        isotopes = {}
        while 1:
            if cnt > n:
                break

            # et = time.time() - st
            # if et < delay:
            #     time.sleep(delay - et)

            # st = time.time()
            size = sock.recv(4)
            size = struct.unpack("i", size)[0]
            str_data = sock.recv(size)

            # self.debug(str_data)
            s = str_data.decode("utf-8")

            self.debug(s)

            s = s.replace("False", '"False"')
            s = s.replace("True", '"True"')
            obj = json.loads(s)

            # read all the buffered messages
            if 'Time' in obj:
                v=datetime.strptime(obj['Time'], '%H:%M:%S %p')
                dt = datetime.now().second - v.second
                if dt > 4 or dt < 0:
                    self.debug(f'skipping {obj}')
                    continue

            # if not i:
            # construct and write the header
            keys = list(obj.keys())

            if "amuNames" not in keys:
                continue

            if not header:
                masses = ["mass({})".format(m) for m in obj["amuNames"]]
                header = (
                    [
                        "count",
                        "time",
                    ]
                    + masses
                    + keys
                )
                writer.writerow(header)

            raw = [obj[h] for h in keys]
            intensities = obj["intensity"]
            ct = time.time()
            for m, si in zip(obj["amuNames"], intensities):
                if m not in isotopes:
                    iso = Isotope(m, "Detector")
                    iso.name = m
                    isotopes[m] = iso
                else:
                    iso = isotopes[m]

                iso.xs = npappend(iso.xs, ct - start_time)
                iso.ys = npappend(iso.ys, si)

            row = (
                [
                    cnt,
                    ct,
                ]
                + intensities
                + raw
            )
            self.debug("sinking row: {}".format(row))
            writer.writerow(row)
            cnt += 1

            et = time.time() - st
            if et < delay:
                time.sleep(delay - et)

        return IsotopeGroup(isotopes=isotopes)

    # def set_data_pump_mode(self, mode):
    #     resp = self.microcontroller.ask('General.DataPump.Mode {}'.format(mode))
    #
    # def halted(self):
    #     """
    #     General.Cycle.Status
    #     1= halt, 5=run multi
    #     """
    #     resp = self.microcontroller.ask('General.Cycle.Status')
    #     if resp:
    #         resp = resp.strip()
    #         return int(resp) == 1
    #
    # def sink_data(self):
    #     packet = self.microcontroller.ask('General.DataPump.Data')
    #
    #     def get_bytes(n):
    #         i = 0
    #         while 1:
    #             yield packet[i:i+n]
    #             i+=n
    #
    #     channel = get_bytes(1)
    #     datatype = get_bytes(1)
    #     status = get_bytes(1)
    #     ndata = get_bytes(1)
    #
    #     timestamp = get_bytes(8)
    #     max_data_tuples = get_bytes(2)
    #     first_mass = get_bytes(2)
    #     last_mass = get_bytes(2)
    #     dwell_speed = get_bytes(1)
    #     measure_unit_mass_resol = get_bytes(1)
    #     ndata_tuples = int(get_bytes(1), 16)
    #
    #     for j in range(ndata_tuples):
    #         intensity = get_bytes(4)
    #         mass = get_bytes(2)
    #         status = get_bytes(1)
    #         adjust_mode = get_bytes(1)
    #
    #     return timestamp, channel, intensity

    def make_configuration_dict(self):
        return {}

    def make_gains_dict(self):
        return {}

    def make_deflection_dict(self):
        return {}

    # def start(self):
    # self.set_integration_time(1, force=True)

    # def finish_loading(self):
    #     super(QuaderaSpectrometer, self).finish_loading()
    # config = self._get_cached_config()
    # if config is not None:
    #     magnet = config['magnet']
    #     # specparams, defl, trap, magnet = ret
    #     mftable_name = magnet.get('mftable')
    #     if mftable_name:
    #         self.debug('updating mftable name {}'.format(mftable_name))
    #         self.magnet.field_table.path = mftable_name
    #         self.magnet.field_table.load_table(load_items=True)

    def _send_configuration(self, **kw):
        pass

    def _get_cached_config(self):
        return {}

    # def get_update_period(self, it=None, is_scan=False):
    #     return self.integration_time * 0.95

    # def cancel(self):
    #     self.debug('canceling')

    # def read_intensities(self, *args, **kw):

    # def read_intensities(self, timeout=60, trigger=False, target='ACQ.B', verbose=False):
    #     self._read_enabled = True
    #     if verbose:
    #         self.debug('read intensities')
    #     resp = True
    #     if trigger:
    #         resp = self.trigger_acq()
    #         if resp is not None:
    #             # if verbose:
    #             #     self.debug(f'waiting {self.integration_time * 0.95} before trying to get data')
    #             # time.sleep(self.integration_time * 0.95)
    #             time.sleep(0.95)
    #             # if verbose:
    #             #     self.debug('trigger wait finished')
    #
    #     keys = []
    #     signals = []
    #     collection_time = None
    #
    #     # self.microcontroller.lock.acquire()
    #     # self.debug(f'acquired mcir lock {self.microcontroller.lock}')
    #     target = '#EVENT:{},{}'.format(target, self.rcs_id)
    #     if resp is not None:
    #         keys = self.detector_names[::-1]
    #         while 1:
    #             line = self.readline()
    #             if line is None:
    #                 break
    #
    #             if verbose:
    #                 self.debug('raw: {}'.format(line))
    #             if line and line.startswith(target):
    #                 args = line[:-1].split(',')
    #                 ct = datetime.strptime(args[4], '%H:%M:%S.%f')
    #
    #                 collection_time = datetime.now()
    #
    #                 # copy to collection time
    #                 collection_time.replace(hour=ct.hour, minute=ct.minute, second=ct.second,
    #                                         microsecond=ct.microsecond)
    #                 try:
    #                     signals = [float(i) for i in args[5:]]
    #                 except ValueError as e:
    #                     self.warning('Failed getting data. error={}'.format(e))
    #
    #                 if verbose:
    #                     self.debug('line: {}'.format(line[:15]))
    #                 break
    #
    #     # self.microcontroller.lock.release()
    #     if len(signals) != len(keys):
    #         keys, signals = [], []
    #     return keys, signals, collection_time

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
        # self.ask('SetAcqPeriod 1000')
        self.integration_time = it

        # if self.integration_time != it or force:
        #     self.ask('StopAcq')
        #     self.debug('setting integration time = {}'.format(it))
        #
        #     self.ask('SetAcqPeriod {}'.format(int(it * 1000)))
        #     self.trait_setq(integration_time=it)

        return it

    # def read_parameter_word(self, keys):
    #     self.debug('read parameter word. keys={}'.format(keys))
    #     values = []
    #     for kk in keys:
    #         try:
    #             key = SOURCE_CONTROL_PARAMETERS[kk]
    #         except KeyError:
    #             values.append(NULL_STR)
    #             continue
    #
    #         resp = self.ask('GetSourceOutput {}'.format(key))
    #         if resp is not None:
    #             try:
    #                 last_set, readback = resp.split(',')
    #                 values.append(float(readback))
    #             except ValueError:
    #                 values.append(NULL_STR)
    #     return values

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01]  # + random(6)
        keys = ["H2", "H1", "AX", "L1", "L2", "CDD"]
        return keys, signals, None

    def _integration_time_default(self):
        self.default_integration_time = QUADERA_DEFAULT_INTEGRATION_TIME
        return QUADERA_DEFAULT_INTEGRATION_TIME


# ============= EOF =============================================
