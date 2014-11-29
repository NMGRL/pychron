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
from pychron.lasers.scanner import Scanner
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================

class AutoTuner(Scanner):
    def _control(self, ydict):
        self.start_control_hook()
        start_delay = ydict['start_delay']
        end_delay = ydict['end_delay']
        setpoints = ydict['setpoints']

        self.set_static_value('Setpoint', 0)
        time.sleep(start_delay)

        tc = self.manager.temperature_controller

        # set autotune parameters
        aggr = ydict['autotune_aggressiveness']
        setpoint = ydict['autotune_setpoint']

        if tc:
            tc.autotune_setpoint = setpoint
            tc.autotune_aggressiveness = aggr

        for t, d in setpoints:
            if self._scanning:
                self.setpoint = t
                self.info('setting setpoint to {} for {}s'.format(t, d))

                if self.manager:
                    self.manager.set_laser_temperature(t)

                self.set_static_value('Setpoint', t, plotid=0)
                st = time.time()
                if tc:
                    self.info('starting autotune')
                    tc.enable_tru_tune = False
                    tc.start_autotune()

                while time.time() - st < d and self._scanning:
                    time.sleep(1)

                if not tc.autotune_finished():
                    self.info('autotuning not completed after {}s. Waiting until finished'.format(d))

                    while not self.autotune_finished():
                        time.sleep(1)

        if tc:
            tc.report_pid()

        if self._scanning:
            self.setpoint = 0
            self.set_static_value('Setpoint', 0)
            if self.manager:
                self.manager.set_laser_temperature(0)

            time.sleep(end_delay)
            self.stop()

        self.end_control_hook(self._scanning)

    def end_control_hook(self, ok):
        pass
    def start_control_hook(self):
        pass

#    def _execute(self):
#        self.info('start autotune scan')
#        tc = self.manager.temperature_controller
#
#        # start autotune
#        tc.start_autotune()


#        self.write(1920, 106, **kw)

#        g = TimeSeriesStreamGraph()
#        sp = 1.5
#        if self.data_manager:
#            self.data_manager.new_frame(base_frame_name='{}_autotune'.format(self.name))

#        g.new_plot(data_limit=180,
#                   scan_delay=sp
#                   )
#        g.new_series()
#        do_later(g.edit_traits)

        # start a query thread
#        self.autotune_timer = Timer(sp * 1000, self._autotune_update, g)
        # self.autotune_timer.Start()

#    def _autotune_update(self, graph):
#        if self.simulation:
#            d = self.get_random_value(0, 100)
#        else:
#            d = self.get_temperature()
#
#        x = graph.record(d)
#        if self.data_manager:
#            self.data_manager.write_to_frame((x, d))
#
#        if self.autotuning and self.autotune_finished():
#            self.autotuning = False
#            self.info('autotuning finished')
#            # requery the device
#            self.initialization_hook()
#            self.acount = 0
#
#        elif self.acount > self.autotuning_additional_recording:
#            # stop the timer n secs after finishing
#            self.autotune_timer.Stop()
#            self.acount = 0
#        else:
#            self.acount += 1

#    def autotune_finished(self, **kw):
#        if self.simulation:
#            try:
#                self.count += 1
#            except AttributeError:
#                self.count = 0
#
#            if self.count > 5:
#                return True
#            else:
#                return False
#
#        r = self.read(1920, response_type='int', **kw)
#        try:
#            return not truefalse_map[str(r)]
#        except KeyError:
#            return True
# ============= EOF =============================================
