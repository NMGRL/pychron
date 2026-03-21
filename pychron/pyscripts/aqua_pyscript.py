# ===============================================================================
# Copyright 2023 ross
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

from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.pyscripts.decorators import makeRegistry
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
from traits.api import Instance
from threading import Event, Thread

command_register = makeRegistry()


class AquaPyScript(ExtractionPyScript):
    data_manager = Instance(CSVDataManager)

    _end_evt = None
    _runthread = None

    def get_command_register(self):
        cs = super().get_command_register()
        return cs + list(command_register.commands.items())

    @command_register
    def start_recording(
        self,
        period=15,
        valve_names=("A", "B"),
        temperature_name="aqua_temperature_controller",
        pressure_name="aqua_pressure_controller",
        actuator_name="aqua_actuator",
    ):
        self.data_manager.new_frame(directory="aqua", base_frame_name="sequence")
        self.data_manager.write_to_frame(
            ["timestamp", "elapsed", "ch2", "ch3", "ch4", "V1_voltage", "V2_voltage"]
        )
        self._end_evt = Event()

        temp_dev = self.get_device(temperature_name)
        pressure_dev = self.get_device(pressure_name)
        valve_actuator = self.get_device(actuator_name)

        self._runthread = Thread(
            target=self._record,
            args=(
                self._end_evt,
                period,
                temp_dev,
                pressure_dev,
                valve_actuator,
                valve_names,
            ),
        )
        self._runthread.start()

    @command_register
    def stop_recording(self):
        if self._end_evt:
            self._end_evt.set()

    def _record(self, evt, period, temp_dev, pressure_dev, actuator, vnames):
        self._aqua_start_timestamp = time.time()
        while not evt.is_set():
            st = time.time()
            row = self._assemble_row(temp_dev, pressure_dev, actuator, vnames)
            self.data_manager.write_to_frame(row)

            p = period - (time.time() - st)
            if p > 0:
                evt.sleep(p)

    def _assemble_row(self, temp_dev, pressure_dev, actuator, vnames):
        # temperatures
        ch2, ch3, ch4 = temp_dev.read_channels([2, 3, 4])

        # pressures

        pressure = pressure_dev.get_pressure()

        # voltages
        va = self.manager.get_valve_by_name(vnames[0])
        vb = self.manager.get_valve_by_name(vnames[1])

        vaf = actuator.get_output_voltage(va)
        vbf = actuator.get_output_voltage(vb)

        # timing
        ts = datetime.now()
        elapsed = time.time() - self._aqua_start_timestamp
        return [ts.isoformat(), elapsed, ch2, ch3, ch4, pressure, vaf, vbf]


# ============= EOF =============================================
