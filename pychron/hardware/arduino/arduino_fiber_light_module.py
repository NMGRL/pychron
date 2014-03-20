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

#============= standard library imports ========================

#============= local library imports  ==========================

from pychron.hardware.core.arduino_core_device import ArduinoCoreDevice
'''
Arduino Sketch fiberlightbox

FiberLight Protocol ver 0.2
4; on
5; off
6,v; set intensity v
7; get intensity      return 1,intensity,v
8; get state          return 1,state,v
9; get version        return 1,0.2

'''


class ArduinoFiberLightModule(ArduinoCoreDevice):
    def power_on(self):
        '''
        '''
        cmd = 4
        cmd = self._build_command(cmd)
        self.ask(cmd)

    def power_off(self):
        '''
        '''
        cmd = 5
        cmd = self._build_command(cmd)
        self.ask(cmd)

    def set_intensity(self, v):
        '''
        '''
        cmd = 6
        cmd = self._build_command(cmd, int(v))
        self.ask(cmd)

    def read_intensity(self):
        resp = self.ask('7;')
        v = self._parse_response(resp)
        if self.simulation:
            v = 50

        if v is None:
            v = 0
        return v / 255.0 * 100

    def read_state(self):
        resp = self.ask('8;')
        v = self._parse_response(resp)
        return bool(v)

    def _parse_response(self, resp):
        if resp is not None:
            try:
                cmd, v = resp.split(',')
                v = v.strip(';')

                if cmd == '1':
                    return int(v)
            except Exception, err:
                print 'parse_response {}'.format(resp), err

    def _build_command(self, cmd, value=None):
        if value is not None:
            return'{},{};'.format(cmd, value)
        else:
            return '{};'.format(cmd)

#============= EOF ====================================
