#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Int
#============= standard library imports ========================
import time
#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class AgilentUnit(CoreDevice):
    slot = Int
    trigger_count = Int
    def load_additional_args(self, config):

        self.slot = self.config_get(config, 'General', 'slot', cast='int', default=1)
        self.trigger_count = self.config_get(config, 'General', 'trigger_count', cast='int', default=1)

    def initialize(self, *args, **kw):
        '''
            Agilent requires chr(10) as its communicator terminator

        '''

        self._communicator.write_terminator = chr(10)
        cmds = (
              '*CLS',
              'FORM:READING:ALARM OFF',
              'FORM:READING:CHANNEL ON',
              'FORM:READING:TIME OFF',
              'FORM:READING:UNIT OFF',
              'TRIG:SOURCE TIMER',
              'TRIG:TIMER 0',
              'TRIG:COUNT {}'.format(self.trigger_count),
#              # 'ROUT:CHAN:DELAY {} {}'.format(0.05, self._make_scan_list()),
              'ROUT:SCAN {}'.format(self.make_scan_list()),
             )

        for c in cmds:
            self.tell(c)

    def make_scan_list(self, *args, **kw):
        raise NotImplementedError

    def _trigger(self, verbose=False):
        '''
        '''
        self.tell('ABORT', verbose=verbose)
        # time.sleep(0.05)
        self.tell('INIT', verbose=verbose)
#        time.sleep(0.075)

    def _wait(self, n=10, verbose=False):
        if self.simulation:
            return True

        for _ in range(n):
            pt = self._points_available(verbose=verbose)
            if pt:
                return pt
            time.sleep(0.005)
        else:
            if verbose:
                self.warning('no points in memory')

    def _points_available(self, verbose=False):
        resp = self.ask('DATA:POINTS?', verbose=verbose)
        if resp is not None and resp:
            return int(resp)
#============= EOF =============================================
#    def read_device(self, **kw):
#        '''
#        '''
#        #resp = super(AgilentADC, self).read_device()
# #        resp = AnalogDigitalConverter.read_device(self)
# #        if resp is None:
#        self._trigger()
#
#        #wait unit points in memory
#        while not self._points_available():
#            time.sleep(0.001)
#

#        resp = self.ask('DATA:POINTS?')
#        if resp is not None:
#            n = float(resp)
#            resp = 0
#            if n > 0:
#                resp = self.ask('DATA:REMOVE? {}'.format(float(n)))
#                resp = self._parse_response_(resp)
#
#            #self.current_value = resp
#            self.read_voltage = resp
#        return resp
