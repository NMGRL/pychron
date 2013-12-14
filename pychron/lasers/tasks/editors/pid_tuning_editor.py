#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
import os
import time

from enable.component_editor import ComponentEditor
from traits.api import Instance
from traitsui.api import View, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.lasers.scanner import Scanner
from pychron.lasers.tasks.editors.laser_editor import LaserEditor
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.paths import paths


class PIDTuningScanner(Scanner):
    _eq_tol = 1.5
    _eq_std = 5

    #def _write_calibration(self, data):
    #    dm = self.csv_data_manager
    #    dm.write_to_frame(data)
    def _stop_hook(self):
        self._set_power_hook(0)

    def _set_power_hook(self, t):
        if self.manager:
            self.manager.set_laser_temperature(t, set_pid=False)

    def start_control_hook(self, ydict):
        self.csv_data_manager = dm = CSVDataManager()
        p = os.path.join(paths.data_dir, 'pid_tune')

        dm.new_frame(directory=p)
        self.debug('Save autotuned pid to {}'.format(dm.get_current_path()))

        aggr = ydict['autotune_aggressiveness']
        setpoint = ydict['autotune_setpoint']
        tc = self.manager.get_device('temperature_controller')
        if tc:
            tc.autotune_setpoint = setpoint
            tc.autotune_aggressiveness = aggr

    def _write_pid_parameters(self, setpoint):
        dm=self.csv_data_manager

        tc = self.manager.get_device('temperature_controller')
        args=tc.report_pid()
        if args:
            ph, pc, i, d=args
            d=(setpoint, ph,pc, i, d)
            dm.write_to_frame(d)

    def _maintain_setpoint(self, t, d):
        if d == 'autotune':
            self._autotune(t)
            self._write_pid_parameters(t)
            self._cool_down()
            #py, tc = self._equilibrate(t)
            #self._write_calibration((t, py, tc))

        else:
            super(PIDTuningScanner, self)._maintain_setpoint(t, d)

    def _cool_down(self):
        """
            wait until temp is below threshold
        """
        self._set_power_hook(0)
        threshold=100
        tm=self.manager.get_device('temperature_monitor')
        ct=tm.get_process_value()
        while ct>threshold:
            time.sleep(0.5)
            ct=tm.get_process_value()

    def _autotune(self, ctemp):
        tc=self.manager.get_device('temperature_controller')

        self.info('starting autotune')
        tc.enable_tru_tune = False
        tc.start_autotune()

        st=time.time()
        while self._scanning:
            sti = time.time()
            if tc.autotune_finished():
                break
            elapsed = time.time() - sti
            time.sleep(max(0.0001, min(1, 1 - elapsed)))

        tc.enable_tru_tune=True
        tt=time.time()-st
        self.info('total tuning time for {}C ={:0.1f}s'.format(ctemp, tt))


class PIDTuningEditor(LaserEditor):
    scanner = Instance(Scanner)

    def stop(self):
        self.scanner.stop()
        self.completed=True

    def _scan_pyrometer(self):
        d = self._pyrometer
        return d.read_temperature(verbose=False)

    def _scan_thermocouple(self):
        d = self._thermocouple
        return d.read_temperature(verbose=False)

    def _scan_power(self):
        d=self._controller
        t,p=d.get_temp_and_power()
        return p
        #return d.read_heat_power(verbose=False)

    def _do_execute(self):
        p = os.path.join(paths.scripts_dir, 'pid_tuning.yaml')
        s = PIDTuningScanner(control_path=p,
                             manager=self._laser_manager)

        s.setup('pid_tuning', 'scan')

        self._pyrometer = self._laser_manager.get_device('pyrometer')
        self._thermocouple = self._laser_manager.get_device('temperature_monitor')
        self._controller=self._laser_manager.get_device('temperature_controller')

        self._controller.use_calibrated_temperature=False

        s.new_function(self._scan_pyrometer, name='pyrometer')
        s.new_function(self._scan_power, name='power')
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

#============= EOF =============================================
