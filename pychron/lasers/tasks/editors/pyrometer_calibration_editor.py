# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= enthought library imports =======================
import os
import time

from enable.component_editor import ComponentEditor
from traits.api import Instance
from traitsui.api import View, UItem

# ============= standard library imports ========================
from numpy import array
# ============= local library imports  ==========================
from pychron.lasers.scanner import Scanner
from pychron.lasers.tasks.editors.laser_editor import LaserEditor
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.paths import paths


class PyrometerCalibrationScanner(Scanner):
    _eq_tol = 1.5
    _eq_std = 5

    def _write_calibration(self, data):
        dm = self.csv_data_manager
        dm.write_to_frame(data)

    def start_control_hook(self, ydict):
        self.csv_data_manager = dm = CSVDataManager()
        p = os.path.join(paths.data_dir, 'pyrometer_calibration')
        dm.new_frame(directory=p)

    def _maintain_setpoint(self, t, d):
        if d == 'equilibrate':
            py, tc = self._equilibrate(t)
            self._write_calibration((t, py, tc))

        else:
            super(PyrometerCalibrationScanner, self)._maintain_setpoint(t, d)

    def _equilibrate(self, ctemp):

        #ctemp=self._current_setpoint
        #ctemp = self.manager.map_temperature(temp)

        py = self.manager.get_device('pyrometer')
        tc = self.manager.get_device('temperature_monitor')
        temps = []
        n = 10
        tol = self._eq_tol
        std = self._eq_std

        while self._scanning:
            sti = time.time()
            #py_t = py.get()
            ref_t = py.temperature
            temps.append(ref_t)
            #            ttemps.append(tc_t)
            ns = array(temps[-n:])
            #            ts = array(ttemps[-n:])
            if abs(ns.mean() - ctemp) < tol and ns.std() < std:
                break

            elapsed = time.time() - sti
            time.sleep(max(0.0001, min(1, 1 - elapsed)))

        nn = 30
        ptemps = []
        ctemps = []
        for _ in range(nn):
            if not self._scanning:
                break

            sti = time.time()

            py_t = py.temperature
            tc_t = tc.process_value

            ptemps.append(py_t)
            ctemps.append(tc_t)
            elapsed = time.time() - sti
            time.sleep(max(0.0001, min(1, 1 - elapsed)))

        return array(ptemps).mean(), array(ctemps).mean()


class PyrometerCalibrationEditor(LaserEditor):
    scanner = Instance(Scanner)

    def stop(self):
        self.scanner.stop()

    def _scan_pyrometer(self):
        d = self._pyrometer
        return d.read_temperature(verbose=False)

    def _scan_thermocouple(self):
        d = self._thermocouple
        return d.read_temperature(verbose=False)

    def _do_execute(self):
        p = os.path.join(paths.scripts_dir, 'pyrometer_calibration.yaml')
        s = PyrometerCalibrationScanner(control_path=p,
                                        manager=self._laser_manager)

        s.setup('pyrometer_calibration', 'scan')

        self._pyrometer = self._laser_manager.get_device('pyrometer')
        self._thermocouple = self._laser_manager.get_device('temperature_monitor')

        s.new_function(self._scan_pyrometer, name='pyrometer')
        s.new_function(self._scan_thermocouple, name='thermocouple')
        #s.new_static_value('Setpoint', 10, plotid=1)

        g = s.make_graph()
        self.component = g.plotcontainer
        if s.execute():
            s.do_scan()
            self.scanner = s
            return True

    def traits_view(self):
        v = View(UItem('component',
                       editor=ComponentEditor()))
        return v

# ============= EOF =============================================
