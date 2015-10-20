# ===============================================================================
# Copyright 2011 Jake Ross
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
import time
from threading import Thread
import os

from traits.api import Any, Property, Bool, Enum, Button
from traitsui.api import View, Item, ButtonEditor
import yaml
from numpy import linspace, array

from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.core.helpers.filetools import unique_path
from pychron.graph.stream_graph import StreamStackedGraph


class LaserScriptExecutor(Loggable):
    laser_manager = Any
    _executing = Bool(False)
    _cancel = False
    execute_button = Button
    execute_label = Property(depends_on='_executing')
    kind = Enum('scan', 'calibration')
    def _kind_default(self):
        return 'scan'
    def _get_execute_label(self):
        return 'Stop' if self._executing else 'Execute'

    def _execute_button_fired(self):
#        name = os.path.join(paths.scripts_dir, '{}_calibration_scan.yaml'.format(self.name))
        self.execute()

    def execute(self):
        if self._executing:
            self._cancel = True
            self._executing = False
        else:
            self._cancel = False
            self._executing = True
            if self.kind == 'scan':
                func = self._execute_scan
            else:
                func = self._execute_calibration
            t = Thread(target=func)
            t.start()

    def _execute_calibration(self):
        name = os.path.join(paths.scripts_dir, '{}_calibration_scan.yaml'.format(self.name))

        import csv
        d = os.path.join(paths.data_dir, 'diode_scans')
        p, _cnt = unique_path(d, 'calibration', extension='csv')
#        st = None
#
#        py = self.laser_manager.pyrometer
#        tc = self.laser_manager.get_device('temperature_monitor')

        g = StreamStackedGraph()
        g.clear()

        g.new_plot(scan_delay=1)
        g.new_series(x=[], y=[])
        g.new_plot(scan_delay=1)
        g.new_series(x=[], y=[], plotid=1)

        self.laser_manager.open_view(g)
        record = False
        if record:
            self.laser_manager.stage_manager.start_recording()
            time.sleep(1)
#        def gfunc(t, v1, v2):
#            g.add_datum((t, v1))
#            g.add_datum((t, v2), plotid=1)

        def gfunc(v1, v2):
            g.record(v1)
            g.record(v2, plotid=1)
        yd = yaml.load(open(name).read())

        start = yd['start']
        end = yd['end']
        step = yd['step']
        mean_tol = yd['mean_tol']
        std = yd['std']
        n = (end - start) / step + 1
#        nn = 30
#
#        py = self.laser_manager.pyrometer
#        tc = self.laser_manager.get_device('temperature_monitor')

        with open(p, 'w') as wfile:
            writer = csv.writer(wfile)
            st = time.time()
            for ti in linspace(start, end, n):
                if self._cancel:
                    break
                args = self._equilibrate_temp(ti, gfunc, st, mean_tol, std)
                if args:
                    self.info('{} equilibrated'.format(ti))
                    py_t, tc_t = args
                    writer.writerow((ti, py_t, tc_t))
                else:
                    break

        self.laser_manager.set_laser_temperature(0)
        if record:
            self.laser_manager.stage_manager.stop_recording()
        self._executing = False

    def _equilibrate_temp(self, temp, func, st, tol, std):
        ''' wait until pyrometer temp equilibrated
        '''

        temps = []
#        ttemps = []
        py = self.laser_manager.pyrometer
        tc = self.laser_manager.get_device('temperature_monitor')

        n = 15

        self.laser_manager.set_laser_temperature(temp)
        ctemp = self.laser_manager.map_temperature(temp)
#        ctemp = self.laser_manager.temperature_controller.map_temperature(temp)
        while 1:
            if self._cancel:
                break
            sti = time.time()
            py_t = py.read_temperature(verbose=False)
            tc_t = tc.read_temperature(verbose=False)
#            t = time.time() - st
            func(py_t, tc_t)


            temps.append(py_t)
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
            if self._cancel:
                break

            sti = time.time()

#            t = sti - st
            py_t = py.read_temperature(verbose=False)
            tc_t = tc.read_temperature(verbose=False)
            func(py_t, tc_t)

            ptemps.append(py_t)
            ctemps.append(tc_t)
            elapsed = time.time() - sti
            time.sleep(max(0.0001, min(1, 1 - elapsed)))

        return array(ptemps).mean(), array(ctemps).mean()
#        return ns.mean(), ts.mean()

    def _execute_scan(self):
        name = os.path.join(paths.scripts_dir, '{}_scan.yaml'.format(self.name))

        import csv
        d = os.path.join(paths.data_dir, 'diode_scans')
        p, _cnt = unique_path(d, 'scan', extension='csv')
        st = None

        py = self.laser_manager.pyrometer
        tc = self.laser_manager.get_device('temperature_monitor')
        yd = yaml.load(open(name).read())

        power = yd['power']
        duration = yd['duration']
        power_on = yd['power_on']
        power_off = yd['power_off']
        period = yd['period']
        if yd.has_key('temp'):
            temp = yd['temp']
        else:
            temp = None

        g = StreamStackedGraph()
        g.new_plot(scan_delay=1,)
        g.new_series(x=[], y=[])
        g.new_plot(scan_delay=1,)
        g.new_series(x=[], y=[], plotid=1)

        self.laser_manager.open_view(g)
        self.laser_manager.stage_manager.start_recording()
        time.sleep(1)
        def gfunc(v1, v2):
            g.record(v1)
            g.record(v2, plotid=1)

        pi = 0
        with open(p, 'w') as wfile:
            writer = csv.writer(wfile)
            t = 0
            ti = 0
            while ti <= duration:
                if self._cancel:
                    break
#                print ti, power_off, pi, ti >= power_off, (ti >= power_off and pi)
                if ti == power_on:
                    # turn on set laser to power
                    if temp:
                        self.laser_manager.set_laser_temperature(temp)
                        pi = temp
                    else:
                        pi = power
                        self.laser_manager.set_laser_power(power)
                elif ti >= power_off and pi:
                    print 'setting power off'
                    if temp:
                        self.laser_manager.set_laser_temperature(0)
                    else:
                        self.laser_manager.set_laser_power(0)
                    pi = 0

                if st is None:
                    st = time.time()

                t = time.time() - st

                py_t = py.read_temperature(verbose=False)
                tc_t = tc.read_temperature(verbose=False)
                gfunc(py_t, tc_t)

                writer.writerow((ti, pi, t, py_t, tc_t))
                ti += 1

                time.sleep(period)

        if temp:
            self.laser_manager.set_laser_temperature(0)
        else:
            self.laser_manager.set_laser_power(0)
        self.laser_manager.stage_manager.stop_recording()
        self._executing = False

    def traits_view(self):
        v = View(Item('execute_button', show_label=False,
                       editor=ButtonEditor(label_value='execute_label'),

                       ),
                 Item('kind', show_label=False)
                 )
        return v

class UVLaserScriptExecutor(LaserScriptExecutor):
    names = Enum('mask', 'z', 'attenuator', 'burst')
    def _execute_button_fired(self):
        n = self.names
        if n is None:
            n = 'mask'

        name = os.path.join(paths.scripts_dir, 'uv_matrix_{}.yaml'.format(n))
        self.execute(name)

    def _execute(self, name):
        self.info('starting LaserScript {}'.format(name))

        lm = self.laser_manager
        sm = lm.stage_manager
        atl = lm.atl_controller

        with open(name, 'r') as rfile:
            def shot(delay=3):
                if not self._cancel:
                    lm.single_burst(delay=delay)

            d = yaml.load(rfile.read())

            device = d['device']
            if device == 'z':
                def iteration(p):
                    sm.set_z(p, block=True)
                    shot()
            elif device == 'laser':
                if self.names == 'trench':
                    atl.set_burst_mode(False)
                else:
                    atl.set_burst_mode(True)

                def iteration(p):
                    if self.names == 'trench':
                        if p == 0:
                            atl.laser_run()
                        else:
                            atl.laser_stop()

                    else:
                        if self.names == 'burst':
                            atl.set_nburst(p, save=False)

                        shot()
            else:
                motor = lm.get_motor(device)
                def iteration(p):
                    motor.trait_set(data_position=p)
                    motor.block(4)
                    shot()

            sx, sy = d['xy']
            xstep = d['xstep']
            ystep = d['ystep']
#            ny=d['y_nsteps']
#            nx=d['x_nsteps']
            ncols = d['ncols']
            ms = d['start']
            me = d['stop']
            mstep = d['step']
            sign = 1
            if me < ms:
                sign = -1

            n = (abs(ms - me) + 1) / mstep

            nx = ncols
            ny = int(n / int(ncols) + 1)

            v = d['velocity']
#            atl.set_nburst(nb)
            dp = ms
            for r in range(ny):
                if self._cancel:
                    break

                for c in range(nx):
                    if self._cancel:
                        break

                    dp = ms + (r * nx + c) * mstep

                    if sign == 1:
                        if dp > me:
                            break
                    else:
                        if dp < me:
                            break

                    x, y = sx + c * xstep, sy + r * ystep

                    # move at normal speed to first pos
                    if r == 0 and c == 0:
                        sm.linear_move(x, y, block=True)
                    else:
                        sm.linear_move(x, y, velocity=v, block=True)

                    if self._cancel:
                        break

                    iteration(dp)
                    if self._cancel:
                        break

                if sign == 1:
                    if dp > me:
                        break
                else:
                    if dp < me:
                        break
            else:
                self.info('LaserScript truncated at row={}, col={}'.format(r, c))

            self._executing = False
            self.info('LaserScript finished'.format(name))

if __name__ == '__main__':
    lm = LaserScriptExecutor()
    name = '/Users/uv/Pychrondata_uv/scripts/uv_laser.yaml'
    lm.execute(name)
