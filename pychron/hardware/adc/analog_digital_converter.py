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

#=============enthought library imports=======================

#=============standard library imports ========================
# import time
#=============local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class AnalogDigitalConverter(CoreDevice):
    '''
    '''
    scan_func = 'read_device'
    read_voltage = 0

    def read_device(self, **kw):
        '''
        '''
        if self.simulation:
            return self.get_random_value()

#    def _scan_(self, *args, **kw):
#        '''
#        '''
#        return self.read_device(**kw)

            # self.stream_manager.record(r, self.name)

# '''
# Agilent requires chr(10) as its communicator terminator
#
# '''
# class AgilentADC(AnalogDigitalConverter):
#    '''
#    '''
# #    def __init__(self, *args, **kw):
# #        super(AgilentADC, self).__init__(*args, **kw)
#    address = None
#
#    def load_additional_args(self, config):
#        '''
#
#        '''
#        #super(AgilentADC, self).load_additional_args(path, setupargs)
#
#        slot = self.config_get(config, 'General', 'slot')
#        channel = self.config_get(config, 'General', 'channel', cast='int')
#
#        #self.address = setupargs[1][0]
#        tc = self.config_get(config, 'General', 'trigger_count', cast='int')
#        self.trigger_count = tc if tc is not None else 1
#        #self.trigger_count = int(setupargs[2][0])
#
#        if slot is not None and channel is not None:
#            self.address = '{}{:02n}'.format(slot, channel)
#            return True
#
#    def initialize(self, *args, **kw):
#        '''
#        '''
#
#        self._communicator.write_terminator = chr(10)
#        if self.address is not None:
#            cmds = [
#                  '*CLS',
#                  'CONF:VOLT:DC (@{})'.format(self.address),
#                  'FORM:READING:ALARM OFF',
#                  'FORM:READING:CHANNEL ON',
#                  'FORM:READING:TIME OFF',
#                  'FORM:READING:UNIT OFF',
#                  'TRIG:SOURCE TIMER',
#                  'TRIG:TIMER 0',
#                  'TRIG:COUNT {}'.format(self.trigger_count),
#                  'ROUT:SCAN (@{})'.format(self.address)
#                 ]
#
#            for c in cmds:
#                self.tell(c)
#
#            return True
#
#    def _trigger_(self):
#        '''
#        '''
#        self.ask('ABORT')
#        #time.sleep(0.05)
#        self.tell('INIT')
#        time.sleep(0.1)
#
#    def read_device(self, **kw):
#        '''
#        '''
#        #resp = super(AgilentADC, self).read_device()
#        resp = AnalogDigitalConverter.read_device(self)
#        if resp is None:
#            self._trigger_()
#            resp = self.ask('DATA:POINTS?')
#            if resp is not None:
#                n = float(resp)
#                resp = 0
#                if n > 0:
#                    resp = self.ask('DATA:REMOVE? {}'.format(float(n)))
#                    resp = self._parse_response_(resp)
#
#                #self.current_value = resp
#                self.read_voltage = resp
#        return resp
#
#    def _parse_response_(self, r):
#        '''
#
#        '''
#        if r is None:
#            return r
#
#        args = r.split(',')
#        data = args[:-1]
#
#        return sum([float(d) for d in data]) / self.trigger_count


class M1000(AnalogDigitalConverter):
    '''
    '''
    short_form_prompt = '$'
    long_form_prompt = '#'
    voltage_scalar = 1
    def load_additional_args(self, config):
        '''

        '''
#        super(M1000, self).load_setup_args(p, setupargs)
#
        self.set_attribute(config, 'address', 'General', 'address')
        self.set_attribute(config, 'voltage_scalar', 'General',
                           'voltage_scalar', cast='float')

        if self.address is not None:
            return True

#    def setup(self):
#        '''
#        '''
#
#        #enable write
#        self.__write__(self.short_form_prompt + addr + 'WE')
#
#        addr = '%02X' % ord(self.address)
#
#        byte2 = '01' #comunications options
#                    #no linefeed, no parity 19200kbs
#        byte3 = '01' #seldom used options
#        btye4 = '%02X' % int('1100000', 2)
#        setupbits = ''.join([addr, byte2, byte3, byte4])
#
#        cmd = 'SU'
#        self.__write__(self.short_form_prompt + addr + cmd + setupbytes)
    def read_device(self, **kw):
        '''
        '''
        res = super(M1000, self).read_device(**kw)
        if res is None:
            cmd = 'RD'
            addr = self.address
            cmd = ''.join((self.short_form_prompt, addr, cmd))

            res = self.ask(cmd, **kw)
            res = self._parse_response_(res)
            if res is not None:
                res /= self.voltage_scalar

        return res

    def _parse_response_(self, r, form='$', type_=None):
        '''
            typical response form 
            short *+00072.00
            long *1RD+00072.00A4
        '''
        func = lambda X: float(X[5:-2]) if form == self.long_form_prompt else float(X[2:])

        if r:
            if type_ == 'block':
                r = r.split(',')
                return [func(ri) for ri in r if ri is not '']
            else:
                return func(r)


class KeithleyADC(M1000):
    '''
    '''
    pass


class OmegaADC(M1000):
    '''
    '''
    def read_block(self):
        '''
        '''
        com = 'RB'
        r = self.ask(''.join((self.short_form_prompt, self.address, com)),
                          remove_eol=False, replace=[chr(13), ','])

        return self._parse_response_(r, type_='block')
#============= EOF =====================================
