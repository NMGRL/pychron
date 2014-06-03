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

#========== standard library imports ==========

import time
#========== local library imports =============
from pychron.hardware.actuators.gp_actuator import GPActuator

"""
disable DTR
1. place 110ohm btw 5V and Reset
2. Cut trace on board RESET-EN

DTR will reset arduino when opening an closing a serial connection
    software init reset allows seamless uploading of sketches 
"""

OPEN = 1
CLOSE = 0


class ArduinoGPActuator(GPActuator):
    """
    Abstract module for Arduino GP Actuator

    @todo: first command to arduino consistently times out

    compatible with valvebox3.pde/Messenger.h
    """

    def open(self, **kw):
        super(ArduinoGPActuator, self).open(**kw)

    def _parse_response(self, resp):
        if resp is not None:
            resp = resp.strip()

        try:
            return int(resp.strip())
        except (TypeError, ValueError, AttributeError):
            return resp

    def _build_command(self, cmd, pin, state):
    #        delimiter = ','
        eol = '\r\n'
        if state is None:
            r = '{} {}{}'.format(cmd, pin, eol)
        else:
            r = '{} {} {}{}'.format(cmd, pin, state, eol)
        return r

    def open_channel(self, obj):
        pin = obj.address
        cmd = ('w', pin, 1)
        self.repeat_command(cmd, ntries=3, check_val='OK')
        return self._check_actuation(obj, True)

    def close_channel(self, obj):
        pin = obj.address
        cmd = ('w', pin, 0)
        self.repeat_command(cmd, ntries=3, check_val='OK')
        return self._check_actuation(obj, False)

    def get_channel_state(self, obj):
        indicator_open_pin = int(obj.address) - 1
        indicator_close_pin = int(obj.address) - 2

        opened = self.repeat_command(('r', indicator_open_pin, None),
                                     ntries=3, check_type=int)

        closed = self.repeat_command(('r', indicator_close_pin, None),
                                     ntries=3, check_type=int)

        err_msg = '{}-{} not functioning properly\nIc (pin={} state={}) does not agree with Io (pin={} state={})'.format(
            obj.name,
            obj.description,
            indicator_close_pin, closed,
            indicator_open_pin, opened)
        try:
            s = closed + opened
        except (TypeError, ValueError, AttributeError):
            return err_msg

        if s == 1:
            return opened == 1
        else:
            return err_msg

    def _check_actuation(self, obj, request):
        if not obj.check_actuation_enabled:
            return True

        if obj.check_actuation_delay:
            time.sleep(obj.check_actuation_delay)

        cmd = 'r'
        if request:
            # open pin
            pin = int(obj.address) - 1
        else:
            pin = int(obj.address) - 2

        state = None
        ntries = 6
        i = 0
        while state is None and i < ntries:
            time.sleep(0.25)
            state = self.repeat_command((cmd, pin, None), ntries=3,
                                        check_type=int)
            i += 1
            if bool(state):
                break

            state = None

        if state is not None:
            return bool(state)

#============= EOF ====================================

#    def get_channel_state(self, obj):
#        '''
#        Query the hardware for the channel state
#
#        '''
#
#        # returns one if channel close  0 for open
#        cmd = 's{}' % obj.name
#        if not self.simulation:
#            s = None
#
#            '''
#            this loop is necessary if the arduino resets on a serial connection
#
#            see http://www.arduino.cc/cgi-bin/yabb2/YaBB.pl?num=1274205532
#
#            arduino will reset can be software initiated using the DTR line (low)
#
#            best solution is to disable DTR reset
#            place 110ohm btw 5V and reset
#
#            leave loop in because isnt harming anything
#            '''
#            i = 0
#            while s is None and i < 10:
#                s = self.ask(cmd, verbose=False)
#                i += 1
#            if i == 10:
#                s = False
#            else:
#                s = '1'
#            return s
#
#
#    def close_channel(self, obj):
#        '''
#        Close the channel
#
#        @type obj: C{HValve}
#        @param obj: valve
#        '''
#        cmd = 'C%s' % obj.name
#        return self.process_cmd(cmd)
#
#    def open_channel(self, obj):
#        '''
#        Open the channel
#
#        @type obj: C{HValve}
#        @param obj: valve
#        '''
#        cmd = 'O%s' % obj.name
#        return self.process_cmd(cmd)
#
#    def process_cmd(self, cmd):
#        '''
#            @type cmd: C{str}
#            @param cmd:
#        '''
#        r = self.ask(cmd) == 'success'
#        if self.simulation:
#            r = True
#        return r
#============= EOF =====================================
