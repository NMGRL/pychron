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
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.data_helper import make_bitarray

SET_BITS = '111'
GET_BITS = '110'
SETPOINT_BITS = '00001'
FAULT_BITS = '01000'
COOLANT_BITS = '01001'

FAULTS_TABLE = ['Tank Level Low',
              'Fan Fail',
              None,
              'Pump Fail',
              'RTD open',
              'RTD short',
              None,
              None]


class ThermoRack(CoreDevice):
    '''
    '''
    convert_to_C = True

    scan_func = 'get_coolant_out_temperature'

    #===========================================================================
    # icore device interface
    #===========================================================================
    def set(self, v):
        pass

    def get(self):
        v = super(ThermoRack, self).get()
#        v = CoreDevice.get(self)
        if v is None:
            if self._scanning:
                v = self.current_scan_value
            else:
                v = self.get_coolant_out_temperature()

        return v

    def write(self, *args, **kw):
        kw['is_hex'] = True
        super(ThermoRack, self).write(*args, **kw)


    def ask(self, *args, **kw):
        '''

        '''
        kw['is_hex'] = True
        return super(ThermoRack, self).ask(*args, **kw)

    def _get_read_command_str(self, b):
        return self._get_command_str(GET_BITS, b)

    def _get_write_command_str(self, b):
        return self._get_command_str(SET_BITS, b)

    def _get_command_str(self, bits, bits_):
        cmd = '{:x}'.format(int(bits + bits_, 2))
        return cmd

    def set_setpoint(self, v):
        '''
            input temp in c
            
            thermorack whats f
        '''
        if self.convert_to_C:
            v = 9 / 5. * v + 32

        cmd = self._get_write_command_str(SETPOINT_BITS)
        self.write(cmd)

        data_bits = make_bitarray(int(v * 10), 16)
        high_byte = '{:02x}'.format(int(data_bits[:8], 2))
        low_byte = '{:02x}'.format(int(data_bits[8:], 2))

        self.write(low_byte)
        self.write(high_byte)

        return cmd, high_byte, low_byte

    def get_setpoint(self):
        '''
        '''
        cmd = self._get_read_command_str(SETPOINT_BITS)
        resp = self.ask(cmd, nbytes=2)
        sp = None
        if not self.simulation and resp is not None:
            sp = self.parse_response(resp, scale=0.1)
        return sp

    def get_faults(self, **kw):
        '''
        '''
        cmd = self._get_read_command_str(FAULT_BITS)
        resp = self.ask(cmd, nbytes=1)

        if self.simulation:
            resp = '0'

        # parse the fault byte
        fault_byte = make_bitarray(int(resp, 16))
#        faults = []
#        for i, fault in enumerate(FAULTS_TABLE):
#            if fault and fault_byte[7 - i] == '1':
#                faults.append(fault)
        faults = [fault for i, fault in enumerate(FAULTS_TABLE)
                    if fault and fault_byte[7 - i] == '1']
        return faults

    def get_coolant_out_temperature(self, **kw):
        '''
        '''
        if not kw.has_key('verbose'):
            kw['verbose'] = False

        cmd = self._get_read_command_str(COOLANT_BITS)

        resp = self.ask(cmd, nbytes=2, **kw)
        if not self.simulation and resp is not None:
            temp = self.parse_response(resp, scale=0.1)
        else:
            temp = self.get_random_value(0, 40)

        return temp

    def parse_response(self, resp, scale=1):
        '''
        '''
        # resp low byte high byte
        # flip to high byte low byte
        # split the response into high and low bytes
        if resp is not None:
            h = resp[2:]
            l = resp[:2]

            resp = int(h + l, 16) * scale
            if self.convert_to_C:
                resp = 5.0 * (resp - 32) / 9.0

        return resp

#============= EOF ====================================
