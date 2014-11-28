# ===============================================================================
# Copyright 2014 Jake Ross
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
# ===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Array, Any, Instance

#============= standard library imports ========================
import struct
import time
from threading import Thread
from numpy import array, vstack
#============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.managers.data_managers.csv_data_manager import CSVDataManager


class ResponseRecorder(HasTraits):
    period = 2
    response_data = Array
    output_data = Array

    _alive = False

    output_device = Any
    response_device = Any
    response_device_secondary = Any
    data_manager = Instance(CSVDataManager)

    _start_time = 0

    def start(self):
        t = time.time()
        self._start_time = t
        self.response_data = array([(t, 0)])
        self.output_data = array([(t, 0)])

        self.data_manager = CSVDataManager()
        self.data_manager.new_frame(base_frame_name='diode_response_tc_control')
        self.data_manager.write_to_frame(('#time', self.output_device.name,
                                          self.response_device.name,
                                          self.response_device_secondary.name))
        t = Thread(target=self.run)
        t.start()

    def run(self):
        self._alive = True
        st = self._start_time
        p = self.period
        rd = self.response_device
        rds = self.response_device_secondary
        od = self.output_device
        dm = self.data_manager

        odata = self.output_data
        rdata = self.response_data
        while self._alive:
            to = time.time()
            t = to - st
            out = od.get_output()
            odata = vstack((odata, (t, out)))

            r = rd.get_response(force=True)
            rdata = vstack((rdata, (t, r)))

            r2 = rds.get_response(force=True)

            datum = (t, out, r, r2)
            datum = map(lambda x: floatfmt(x, n=3), datum)
            dm.write_to_frame(datum)
            et = time.time() - to
            slt = p - et - 0.001
            if slt > 0:
                time.sleep(slt)

        self.output_data = odata
        self.response_data = rdata

    def stop(self):
        self._alive = False
        if self.data_manager:
            self.data_manager.close_file()

    def get_response_blob(self):
        if len(self.response_data):
            return ''.join([struct.pack('<ff', x, y) for x, y in self.response_data])

    def get_output_blob(self):
        if len(self.output_data):
            return ''.join([struct.pack('<ff', x, y) for x, y in self.output_data])

# ============= EOF =============================================
