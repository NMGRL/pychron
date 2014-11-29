# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Float
from traitsui.api import View, Item
# ============= standard library imports ========================
import time
import numpy as np
from ConfigParser import ConfigParser
import os
# ============= local library imports  ==========================
from pychron.spectrometer.jobs.spectrometer_task import SpectrometerTask
from pychron.graph.graph import Graph
from pychron.core.time_series.time_series import smooth
from pychron.globals import globalv
from pychron.paths import paths


def scan_generator(start, stop, n):
    d = stop - start
    d3 = d / 3
    xs = np.linspace(start, stop, n)
    ys = ((xs - d3) / d) ** 3 + 1 * xs / d + 5 + np.random.random(n) / 80

    i = 0
    while 1:
        yield ys[i]
        i += 1

class CDDOperatingVoltageScan(SpectrometerTask):
    start_v = Float(0)
    end_v = Float(1500)
    step_v = Float(1)
    title = 'CDD Operating Voltage Scan'
    def _execute(self):
        spec = self.spectrometer
        graph = self.graph
        steps = self._calc_step_values(self.start_v, self.end_v, self.step_v)
        settle_time = 1

        scan_gen = scan_generator(steps[0], steps[-1], len(steps))
        for opv in steps:
            if globalv.spectrometer_debug:
                v = scan_gen.next()
                settle_time = 0.001
            else:
                spec.set_cdd_operating_voltage(opv)
                v = spec.get_intensity('CDD')

            graph.add_datum((opv, v), do_after=1)
            time.sleep(settle_time)

        xs = graph.get_data()
        ys = graph.get_data(axis=1)

        nopv = self._calculate_optimal_operating_voltage(xs, ys)

        if nopv:
            self.info('Optimal operating voltage {:0.1f}'.format(nopv))

            graph.add_vertical_rule(nopv, color=(0, 0, 1))

            if self.confirmation_dialog('Save new CDD Operating voltage {:0.1f}'.format(nopv)):
                self._save(nopv)

    def _save(self, nv):
        p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        config = ConfigParser()
        config.read(p)

        config.set('CDDParameters', 'OperatingVoltage', nv)
        config.write(open(p, 'w'))
        self.info('saving new operating voltage {:0.1f} to {}'.format(nv, p))

    def _calculate_optimal_operating_voltage(self, xs, ys):
        '''
             find the flattest region of the grad

            1. smooth the signal
            2. calculate the gradient 
            3. get x of min y
            
            @todo: this algorithm may not work properly. need to collect a real scan to test on
            
        '''

        # 1. smooth
        smoothed = smooth(ys, window_len=100)

        # truncate the smooth to elimate edge artifacts
        trunc = 20
        xs = xs[trunc:-trunc]
        smoothed = smoothed[trunc:-trunc]

        self.graph.new_series(xs, smoothed)

        # 2. gradient
        grads = np.gradient(smoothed)

        # 3. get min
        cp = xs[np.argmin(grads)]

        return cp


    def _graph_factory(self):
        graph = Graph(container_dict=dict(padding=5,
                                          bgcolor='lightgray'))

        graph.new_plot(
                       padding=[50, 5, 5, 50],
#                       title='{}'.format(self.title),
                       xtitle='CDD Operating Voltage (V)',
                       ytitle='Intensity (fA)',
                       )
        graph.new_series(type='scatter',
                         marker='pixel')
        return graph

    def traits_view(self):
        v = View(Item('start_v', label='Start Voltage'),
                   Item('end_v', label='Stop Voltage'),
                   Item('step_v', label='Step Voltage'),
                   title=self.title,
                   buttons=['OK', 'Cancel']
                  )
        return v



if __name__ == '__main__':

    xs = np.linspace(0, 100, 200)
    ys = xs[:50]
    b = ys[-1]
    ys2 = xs[50:150] * 0.001 + b
    ys3 = xs[150:] - 50

    ys = np.hstack((ys, ys2, ys3))
    c = CDDOperatingVoltageScan()
    v = c._calculate_optimal_operating_voltage(xs, ys)

    assert(abs(v - 49.4974874372) < 0.001)

# ============= EOF =============================================
