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
from traits.api import List, Event, Float, Str, Bool, Property, \
    Any
from traitsui.api import View, Item, spring, HGroup, Label, VGroup, Spring, \
    ButtonEditor, EnumEditor
#============= standard library imports ========================
import time
import os
#============= local library imports  ==========================
from pychron.helpers.timer import Timer
from pychron.paths import paths
from watlow_ezzone import WatlowEZZone
from pychron.pychron_constants import NULL_STR
from pychron.pyscripts.bakeout_pyscript import BakeoutPyScript
from pychron.ui.led_editor import LEDEditor, ButtonLED
# from pychron.ui.led_editor import ButtonLED, LEDEditor

# class BakeoutMonitor():
#    pass
# class WarningMessge(HasTraits):
#    message = Str
#    def traits_view(self):
#        v=View(HGroup(Item('image'),
#
#                      )


BLANK_SCRIPT = NULL_STR


class BakeoutController(WatlowEZZone):
    """

        bakeout controller can be operated in one of two modes.

        Mode 1 is used when no script is specified and both a valid setpoint and duration are set.
        The controller will open loop set to the setpoint. After duration minutes have passed the
        controller sets to 0

        Mode 2 is used when a script is set.
        The controller uses a BakeoutTimerScript to heat and cool ramp to setpoints.

        psuedo script
        goto_setpoint('heat')
        maintain()
        goto_setpoint('cool')

    """
    duration = Property(Float(enter_set=True, auto_set=False),
                        depends_on='_duration')
    _duration = Float

    setpoint = Float(enter_set=True, auto_set=False)

    scripts = List()
    script = Str(BLANK_SCRIPT)
    #    led = Instance(LED, ())
    #     led = Instance(ButtonLED, ())
    led = Any

    #    alive = Bool(False)
    active = Bool(False)
    cnt = 0
    ramp_scale = None

    update_interval = Float(1)
    process_value_flag = Event

    _active_script = None
    _oduration = 0

    record_process = Bool(False)

    # max_output = Property(Float(enter_set=True, auto_set=False),
    #                       depends_on='_max_output')
    # _max_output = Float(100)
    _duration_timeout = False

    _timer = None

    state_button = Event
    state_label = Property(depends_on='active')

    state_enabled = Property(depends_on='ok_to_run, _state_enabled')
    _state_enabled = Bool

    ok_to_run = Property
    execute_dirty = Event
    user_cancel = Bool

    heating = False
    _check_buffer = None
    _check_temp_enabled = True
    _check_temp_minutes = 2
    _check_temp_threshold = 40
    _check_start_minutes = 5
    default_output = 2

    #    (depends_on='_ok_to_run')
    #    _ok_to_run = Bool(False)



    def initialization_hook(self):
        '''
            suppress the normal initialization querys
            they are not necessary for the bakeout manager currently
        '''
        # read the current max output setting
        # p = self.read_high_power_scale()
        # if p:
        #     self._max_output = p

            #    def isAlive(self):
            #        return self.alive

    def isActive(self):
        return self.active

    #    def kill(self):
    #        self.led.state = 'red'
    # #        if self.isAlive() and self.isActive():
    #        if self.isActive():
    #            self.info('killing')
    #            if self._active_script is not None:
    #                self._active_script._alive = False
    #
    #            if abs(self.setpoint) > 0.001:
    #                self.set_closed_loop_setpoint(0)

    def load_additional_args(self, config):
        '''
        '''
        self.load_scripts()

        self.set_attribute(config, '_check_temp_enabled', 'Monitor', 'enabled', cast='boolean', default=True)
        self.set_attribute(config, '_check_temp_minutes', 'Monitor', 'time', cast='float', default=2)
        self.set_attribute(config, '_check_temp_threshold', 'Monitor', 'threshold', cast='float', default=40)
        self.set_attribute(config, '_check_start_minutes', 'Monitor', 'start_time', cast='float', default=5)

        return True


    def load_scripts(self):
        sd = os.path.join(paths.scripts_dir, 'bakeout')
        if os.path.isdir(sd):
            files = os.listdir(sd)
            #            s = [f for f in files
            #                        if not os.path.basename(f).startswith('.') and
            #                             os.path.splitext(f)[1] in ['.py', '.bo']]
            #            print s
            s = [NULL_STR] + [f for f in files if not f.startswith('.') and
                                                  os.path.isfile(os.path.join(sd, f)) and
                                                  os.path.splitext(f)[1] in ['.py', '.bo']]
            self.scripts = s

        else:
            self.scripts = [NULL_STR]
            if self.confirmation_dialog('Default Bakeout script directory does not exist. \
Add {}'.format(sd)):
                os.mkdir(sd)

    def _get_ok_to_run(self):
        ok = True
        if not self.record_process:
            if self.script == NULL_STR:
                ok = not (self.setpoint == 0 or self.duration == 0)
        else:
            ok = not self.duration == 0

        return ok

    def on_led_action(self):
    #        if self.isAlive():
        if self.isActive():
            self.end()
        else:
            self.led.state = 'red'

    def run(self):
        '''
        '''
        self.cnt = 0
        self.start_time = time.time()
        self.active = True

        self._check_buffer = []

        # set led to green
        self.led.state = 'green'
        if self.script == NULL_STR:
            self._active_script = None
            self.heating = True
            self._duration_timeout = True
            self.set_control_mode('closed')
            self.set_closed_loop_setpoint(self.setpoint)
            self._oduration = self._duration

        else:
            self.heating = False
            self._duration_timeout = False

            #            if self._active_script is not None:
            #                self._active_script.cancel()

            t = BakeoutPyScript(root=os.path.join(paths.scripts_dir,
                                                  'bakeout'),
                                name=self.script,
                                controller=self)

            self.info('executing script {}, {}'.format(t.name, t.root))
            t.bootstrap()
            t.execute(new_thread=True, finished_callback=self.end)

            self._active_script = t

    def stop_timer(self):
        if self._timer is not None:
            self._timer.Stop()
            self.info('stop timer')

    def start_timer(self):
        if self._timer is not None:
            self._timer.Stop()
            # wait for timer to exit
            time.sleep(0.05)

        self.info('starting update timer')
        self._timer = Timer(self.update_interval * 1000., self._update_)

    def ramp_to_setpoint(self, ramp, setpoint, scale):
        '''
        '''
        if scale is not None and scale != self.ramp_scale:
            self.ramp_scale = scale
            self.set_ramp_scale(scale)

        self.set_ramp_action('setpoint')
        self.set_ramp_rate(ramp)
        self.set_closed_loop_setpoint(setpoint)
        self.setpoint = setpoint

    def set_ramp_scale(self, value, **kw):
        '''
        '''
        scalemap = {'h': 39,
                    'm': 57}

        if 'value' in scalemap:
            self.info('setting ramp scale = {}'.format(value))
            value = scalemap[value]
            register = 2188
            self.write(register, value, nregisters=2, **kw)

    def set_ramp_action(self, value, **kw):
        '''
        '''
        rampmap = {'off': 62,
                   'startup': 88,
                   'setpoint': 1647,
                   'both': 13}

        if value in rampmap:
            self.info('setting ramp action = {}'.format(value))
            value = rampmap[value]
            register = 2186
            self.write(register, value, nregisters=2, **kw)

    def set_ramp_rate(self, value, **kw):
        '''
        '''
        self.info('setting ramp rate = {:0.3f}'.format(value))
        register = 2192
        self.write(register, value, nregisters=2, **kw)

    def end(self, user_kill=False, script_kill=False, msg=None, error=None):

        if self.isActive():
            if msg is None:
                msg = 'bakeout finished'
                self.info(msg)

            if user_kill:
                msg = '{} - Canceled by user'.format(msg)
                self.info(msg)
            elif error:
                self.warning(error)

            self.led.state = 'red'

            if self._active_script is not None:
                self._active_script.cancel()
                self._active_script = None

            self.setpoint = 0
            self._duration = 0
            self.active = False
            self.state_enabled = False

    def get_temp_and_power(self, **kw):
        pr = super(BakeoutController, self).get_temp_and_power(**kw)
        self.process_value_flag = True
        return pr

    def get_temperature(self, **kw):
        t = super(BakeoutController, self).get_temperature(**kw)
        self.process_value_flag = True
        return t

    def _update_(self):
        '''
        '''
        if self.isActive():
            self.cnt += self.update_interval
            nsecs = 15
            if self.cnt >= nsecs:
                self._duration -= (nsecs + self.cnt % nsecs) / 3600.
                self.cnt = 0

        # self.get_temperature(verbose=False)
        # self.complex_query(verbose=False)
        self.get_temp_and_power(verbose=False)
        if self._check_temp_enabled:
            self._check_temp()
            #        self.get_temp_and_power(verbose=True)

        if self._duration_timeout:
            if time.time() - self.start_time > self._oduration * 3600.:
                self.end()

    def _check_temp(self):
        if self.isActive() and self.heating:
            n = int(self._check_temp_minutes * 60 / float(self.update_interval))
            st = int(self._check_start_minutes * 60 / float(self.update_interval))
            cb = self._check_buffer
            cb.append(self.process_value)
            if len(cb) >= st:
                cb = cb[-n:]
                avgtemp = sum(cb) / len(cb)
                if avgtemp < self._check_temp_threshold:

                    if self._active_script is not None:
                        self._active_script.cancel()

                    self.setpoint = 0
                    self._duration = 0

                    self.led.state = False
                    self.active = False

                    #                    self.alive = False
                    self.warning('controller failed to heat average temp= {}, duration={}'.format(avgtemp,
                                                                                                  self._check_temp_minutes))
                    self.warning_dialog(
                        'Controller failed to heat. Average temp.={:0.1f} after {} minutes. Check thermocouple and heating tape'. \
                            format(avgtemp, self._check_temp_minutes), sound='alarm1')

            self._check_buffer = cb
            #===============================================================================
            # handlers
            #===============================================================================

    def _state_button_fired(self):
    #        if self.isAlive():
        if self.isActive():
            self.user_cancel = True
            self.end()
        else:
            self.user_cancel = False
            self.run()

        self.execute_dirty = True

    def _setpoint_changed(self):
        if self.isActive():
            self.set_closed_loop_setpoint(self.setpoint)

    def _script_changed(self):
        self._duration = 0
        self.setpoint = 0
        self.execute_dirty = True

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_state_label(self):
    #        return 'Stop' if self.isAlive() else 'Start'
        return 'Stop' if self.isActive() else 'Start'

    def _get_duration(self):
        return self._duration

    def _set_duration(self, v):
    #        if self.isAlive():
        if self.isActive():
            self._oduration = v
            self.start_time = time.time()
        else:
            self.execute_dirty = True

        self._duration = v

    def _validate_duration(self, v):
        try:
            value = float(v)
        except ValueError:
            value = self._duration

        return value

    def _set_state_enabled(self, s):
        self._state_enabled = s

    def _get_state_enabled(self):
        return self.ok_to_run and self._state_enabled

    #===============================================================================
    # defaults
    #===============================================================================
    def _led_default(self):
        return ButtonLED(callable=self.on_led_action)

    #============= views ===================================
    def traits_view(self):
        '''
        '''
        state_item = Item('state_button',
                          editor=ButtonEditor(label_value='state_label'),
                          show_label=False,
                          enabled_when='state_enabled'
        )
        show_label = False
        if self.name.endswith('1'):
            show_label = True
            header_grp = HGroup(
                Spring(width=95, springy=False),
                HGroup(
                    Label(self.name[-1]),
                    Item('led', editor=LEDEditor(),
                         show_label=False, style='custom'),
                    state_item,
                ),
            )
            process_grp = HGroup(
                Spring(width=35, springy=False),
                Label('Temp. (C)'),
                spring,
                Item('process_value', show_label=False,
                     style='readonly', format_str='%0.1f'),
                spring,
            )
        else:
            header_grp = HGroup(
                HGroup(
                    Label(self.name[-1]),
                    Item('led', editor=LEDEditor(),
                         show_label=False, style='custom'),
                    state_item,
                    #                                Item('color', show_label=False, style='readonly')
                ),
            )
            process_grp = HGroup(
                spring,
                Item('process_value', label='Temp (C)',
                     show_label=False,
                     style='readonly', format_str='%0.1f'),
                spring,
            )
        v = View(
            VGroup(
                header_grp,
                VGroup(
                    Item('script', show_label=False,
                         editor=EnumEditor(name='scripts'),
                         width=-200,
                         enabled_when='not active'
                    ),
                    Item('duration', label='Duration (hrs)',
                         show_label=show_label,
                         enabled_when='script=="---"',
                         format_str='%0.3f'),
                    Item('setpoint', label='Setpoint (C)',
                         show_label=show_label,
                         enabled_when='script=="---"',
                         format_str='%0.2f'),
                    Item('max_output', label='Max.Out (%)',
                         format_str='%0.2f',
                         show_label=show_label,
                         enabled_when='not active'),
                    process_grp
                ),
            )
        )
        return v

        #============= EOF ====================================
