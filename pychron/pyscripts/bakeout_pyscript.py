#===============================================================================
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
#===============================================================================



#============= enthought library imports =======================
from traits.api import Any
#============= standard library imports ========================
from numpy import linspace
#============= local library imports  ==========================
from pychron.pyscripts.pyscript import PyScript, makeRegistry, verbose_skip
import time


TIMEDICT = dict(s=1, m=60.0, h=60.0 * 60.0)
command_register = makeRegistry()

class BakeoutPyScript(PyScript):
    controller = Any

    _current_setpoint = 0

    def calculate_graph(self):
        xs, ys = self._calculate_graph()

        # convert to hours
        xs = [xi / 3600. for xi in xs]
        from pychron.graph.graph import Graph
        g = Graph(container_dict=dict(padding=[50, 10, 10, 50],
                                      bgcolor='gray'),
                   window_title='Bakeout Profile'
                  )
        g.new_plot(xtitle='Time (hrs)',
                   ytitle='Temperature (C)',
                   )
        g.new_series(xs, ys)
        g.set_y_limits(min(ys), max(ys), pad=10)
        g.edit_traits()

    def _calculate_graph(self):
        self._xs = [0]
        self._ys = [0]
        self._graph_calc = True
        self.bootstrap()
        self.test()
        return self._xs, self._ys

    def get_command_register(self):
        return command_register.commands.items()

    @verbose_skip
    @command_register
    def ramp(self, temperature=0, rate=0, start=None, period=60):
        temperature = float(temperature)
        rate = float(rate)
        period = float(period)

#        if self._graph_calc:
#
#            xs = self._xs[-1]
#            ds = temperature - self._current_setpoint
#            self._current_setpoint = temperature
#
#            dx = ds / (rate / 3600.)
#            self._xs.append(xs + dx)
#            self._ys.append(temperature)
#            return

        if self._cancel:
            return

        c = self.controller
        if start is None:
            start = 25
            if c is not None:
                # possible to just read the process_value
                # for now force a query to the device
                t = c.get_temperature()
                if t is not None:
                    ctemp = int(t)
                    start = max(start, ctemp)

        self.info('ramping from {} to {} rate= {} C/h, period= {} s'.format(start,
                                                                    temperature,
                                                                    rate,
                                                                    period
                                                                    ))

        dT = temperature - start
        dur = abs(dT / rate)
        if c is not None:
            c.duration = dur
            if rate > 0:
                c.heating = True
            else:
                c.heating = False
        # convert period to hours
#        hperiod = period / 3600.
#        steps = linspace(start, temperature, dur * 3600 / float(period))

        check_period = 0.5
        samples_per_hr = 3600 / float(period)
        steps = linspace(start, temperature, dur * samples_per_hr)
        for si in steps:
            if self._cancel:
                break
            self._set_setpoint(si)
            if period > 5:
                for _ in xrange(int(period / check_period)):
                    if self._cancel:
                        break
                    time.sleep(check_period)
                else:
                    continue
                break
            else:
                time.sleep(period)

    @verbose_skip
    @command_register
    def setpoint(self, temperature=0, duration=0, units='h'):

        ts = TIMEDICT[units]
#        if self._graph_calc:
#            self._current_setpoint = temperature
#            self._xs.append(self._xs[-1])
#            self._xs.append(self._xs[-1] + duration * ts)
#            self._ys.append(temperature)
#            self._ys.append(temperature)
#            return

        if self._cancel:
            return

        # convert duration from units to seconds

        duration *= ts
        self.info('setting setpoint to {} for {}'.format(temperature, duration))
        c = self.controller
        if c is not None:

            self._set_setpoint(temperature)
            # convert back to hours
            c.trait_set(duration=duration / 3600.,
                                 heating=True)

        self._block(duration)

    def _set_setpoint(self, sp):
        self.info('setting setpoint to {}'.format(sp))
        c = self.controller
        if c is None:
            return

        if c.setpoint == sp:
            c.set_closed_loop_setpoint(sp)
        else:
            c.setpoint = sp
#============= EOF ====================================
