#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Array, Any

#============= standard library imports ========================
import struct
import time
from threading import Thread
from numpy import array, vstack

#============= local library imports  ==========================
from pychron.managers.data_managers.csv_data_manager import CSVDataManager


class ResponseRecorder(HasTraits):
    period = 2
    response_data = Array
    output_data = Array

    _alive = False

    output_devce = Any
    response_device = Any
    response_device_secondary = Any

    def start(self):
        t = time.time()
        self.response_data = array([(t, 0)])
        self.output_data = array([(t, 0)])

        self.dm = CSVDataManager()
        self.dm.new_frame(base_frame_name='diode_response')
        self.dm.write_to_frame(('#time', self.output_devce.name,
                                self.response_device.name,
                                self.response_device_secondary.name))
        t = Thread(target=self.run)
        t.start()

    def run(self):
        self._alive = True
        while self._alive:
            t = time.time()
            out = self.output_device.get_output()
            self.output_data = vstack((self.output_data, (t, out)))

            r = self.response_device.get_response(force=True)
            self.response_data = vstack((self.response_data, (t, r)))

            r2 = self.response_device_secondary.get_response(force=True)

            self.dm.write_to_frame((t, out, r, r2))
            time.sleep(self.period)

    def stop(self):
        self._alive = False
        self.dm.close_file()

    def get_response_blob(self):
        if len(self.response_data):
            return ''.join([struct.pack('<ff', x, y) for x, y in self.response_data])

    def get_output_blob(self):
        if len(self.output_data):
            return ''.join([struct.pack('<ff', x, y) for x, y in self.output_data])

#============= EOF =============================================
