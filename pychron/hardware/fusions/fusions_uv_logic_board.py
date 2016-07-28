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

# ============= enthought library imports =======================
# from traits.api import Instance, DelegatesTo
from traits.api import Any, Int, Instance, Property, Event, \
    Enum, String
from traitsui.api import View, Item, VGroup, ButtonEditor, HGroup, Spring
# ============= standard library imports ========================
# ============= local library imports  ==========================
from fusions_logic_board import FusionsLogicBoard
from threading import Timer, Event as TEvent
from pychron.hardware.kerr.kerr_device import KerrDevice
from pychron.core.ui.led_editor import LEDEditor, LED

from pychron.core.ui.custom_label_editor import CustomLabel
from datetime import datetime, timedelta

# from pychron.hardware.kerr.kerr_motor import KerrMotor
FLOW_STATES = {'on': 'Stop Flow', 'off': 'Start Flow', 'purge': 'Purging'}


class NitrogenFlower(KerrDevice):
    delay = Int(10)
    timeout = Int(10)
    controller = Any
    channel = Int
    _ready_signal = None
    _timeout_timer = None
    _delay_timer = None
    _lock = None
    _cancel_signal = None
    #     _cancel = False

    flow_button = Event
    flow_label = Property(depends_on='_flow_state')
    _flow_state = Enum('off', 'purge', 'on')

    led = Instance(LED, ())

    message = String

    def _flow_button_fired(self):
        #        print self._flowing, 'asdfasdfsa'
        if self._flow_state in ('on', 'purge'):
            self.stop()
        elif self._flow_state == 'off':
            self.start()

    def _get_flow_label(self):
        return FLOW_STATES[self._flow_state]

    def stop(self):
        if self._delay_timer:
            self._delay_timer.cancel()
        if self._timeout_timer:
            self._timeout_timer.cancel()

        self._ready_signal.clear()
        self._stop_flow()

        self._set_state_off()

    def _set_state_off(self):
        self._flow_state = 'off'
        self.led.state = 0
        self.message = ' '

    def _set_state_on(self):
        self._flow_state = 'on'
        self.led.state = 2
        t = datetime.now()
        d = timedelta(seconds=self.timeout)
        t = t + d
        st = t.strftime('%H:%M:%S')
        self.message = 'Timeout at {}'.format(st)

    def _set_state_purge(self):
        self._flow_state = 'purge'
        self.led.state = 1
        self.message = 'Purging for 10s'

    def start(self):
        if self._flow_state == 'on':
            # reset the timeout timer
            self._start_timeout_timer()
        elif self._flow_state == 'purge':
            pass
        else:
            # start purge
            self._start_flow()

            self._set_state_purge()

            #             self._flow_state = 'purge'
            #             self.led.state = 1
            self._start_delay_timer()

        #         if self._ready_signal is None:
        #             self._ready_signal=TEvent()
        #
        #         if self._lock is None:
        #             self._lock=Lock()
        #
        #         if self._cancel_signal is None:
        #             self._cancel_signal=TEvent()
        #
        #         if not self._ready_signal.is_set():
        #             self._start_delay_timer()
        #             self.led.state=1
        #             do_later(self.trait_set, _flow_state='purge',
        #                      message='Purging for {}s'.format(self.delay)
        #                      )
        #         else:
        #             #cancel current timeout timer
        # #             self._cancel_signal.set()
        # #             time.sleep(1)
        #             #reset timer
        #
        #             with self._lock:
        #                 self._timeout_timer=0
        # #             self._start_timeout_timer()
        #
        #     def stop(self):
        #         if self._delay_timer:
        #             self._delay_timer.cancel()
        #         if self._timeout_timer:
        #             self._timeout_timer.cancel()
        #
        #         self._cancel_signal.set()
        #         self._ready_signal.clear()
        #
        #         self._stop_flow()
        #         self.led.state = 0
        #         do_later(self.trait_set, _flow_state='off',
        #                                 message='',
        # #                                 _cancel=True
        #                                 )
        # #        self._flow_state='off'

    def _start_flow(self):
        self._set_io_state(self.channel, False)

    def _stop_flow(self):
        self._set_io_state(self.channel, True)

    def _start_delay_timer(self):
        self._ready_signal = TEvent()
        self._ready_signal.clear()
        self._delay_timer = Timer(self.delay, self.set_ready, args=(True,))
        #         self._start_timeout_timer()
        self._delay_timer.start()

    def _start_timeout_timer(self):
        #         def _loop(lock, cancel):
        #             with lock:
        #                 self._timeout_cnt = 0
        #
        #             while self._timeout_cnt < self.timeout and not cancel.is_set():
        #                 v = self.timeout - self._timeout_cnt
        #                 do_later(self.trait_set, message='Timeout after {}s ({}s) '.format(self.timeout, v))
        #                 with lock:
        #                     self._timeout_cnt += 1
        #
        #                 time.sleep(1)
        #
        #             if self._timeout_cnt >= self.timeout:
        #                 do_later(self.trait_set, message='Timed out after {}s'.format(self.timeout))
        #                 self.set_ready(False)
        #
        #         t = Thread(target=_loop, args=(self._lock, self._cancel_signal))
        #         t.start()
        if self._timeout_timer:
            self._timeout_timer.cancel()

        #         self._timeout_timer = Timer(10, self.set_ready, args=(False,))
        self._timeout_timer = Timer(self.timeout, self.set_ready, args=(False,))
        self._timeout_timer.start()

    def set_ready(self, onoff):
        if onoff:
            self._ready_signal.set()
            #             self.led.state = 2

            self._set_state_on()

            #             do_later(self.trait_set, _flow_state='on',
            #                     message='Timeout at {}'.format(st)
            #                      )

            self._start_timeout_timer()
        else:
            self.stop()
            self._ready_signal.clear()

    def is_ready(self):
        if self._ready_signal:
            return self._ready_signal.is_set()

    def traits_view(self):
        v = View(HGroup(Item('led', editor=LEDEditor(),
                             show_label=False, style='custom'),
                        Item('flow_button',
                             show_label=False,
                             editor=ButtonEditor(label_value='flow_label')),
                        Spring(springy=False, width=20),
                        CustomLabel('message',
                                    color='maroon', size=14,
                                    springy=True)))
        return v


class FusionsUVLogicBoard(FusionsLogicBoard):
    """
    """
    has_pointer = False
    _test_comms = False  # dont test comms on startup. UV doesn't really have logic board only kerr motor controllers

    nitrogen_flower = Instance(NitrogenFlower)

    def _nitrogen_flower_default(self):
        return NitrogenFlower(parent=self)

    def _enable_laser(self, **kw):
        """
        """
        return True

    def _disable_laser(self):
        """
        """
        return True

    def prepare(self):
        self.nitrogen_flower.start()
        return True

    def is_ready(self):
        return self.nitrogen_flower.is_ready()

    #    attenuator_motor = Instance(KerrMotor, ())
    #    attenuation = DelegatesTo('attenuator_motor', prefix='data_position')
    #    attenuationmin = DelegatesTo('attenuator_motor', prefix='min')
    #    attenuationmax = DelegatesTo('attenuator_motor', prefix='max')
    #    update_attenuation = DelegatesTo('attenuator_motor', prefix='update_position')

    def load_additional_args(self, config):
        if super(FusionsUVLogicBoard, self).load_additional_args(config):
            # load nitrogen flower

            nf = self.nitrogen_flower
            section = 'Flow'
            if config.has_section(section):
                nf.delay = self.config_get(config, section, 'delay', cast='int', default=30)
                nf.timeout = self.config_get(config, section, 'timeout', cast='int', default=6000)
                nf.channel = self.config_get(config, section, 'channel', cast='int', default=1)
                nf.address = self.config_get(config, section, 'address', default='01')
            return True

    def get_control_group(self):
        cg = super(FusionsUVLogicBoard, self).get_control_group()

        ng = VGroup(Item('nitrogen_flower', show_label=False, style='custom'),
                    cg
                    )
        return ng

# ============= views ===================================

# ============= EOF ====================================
