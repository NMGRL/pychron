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
from traits.api import Float, Property, Button, Bool, Str
from traitsui.api import Item, spring, Group, HGroup, \
    RangeEditor, ButtonEditor
#=============standard library imports ========================

#=============local library imports  ==========================
from core.core_device import CoreDevice


class MikronGA140Pyrometer(CoreDevice):
    '''
    emissivity (Emi) = 100%;
    exposition time (t90) = min;
    clear time (tClear) = off;
    analog output (mA) = 0 ... 20 mA; 
    sub range (from / to) same as temperature range 
    address (Adr) = 00; baud rate (Baud) = 19200 Bd; 
    temperature display (C / F) = C
    wait time (tw) at RS232 = 00; 
    wait time (tw) at RS485 = 10; 
    switch for serial interface (RS485 / RS232) = RS232
    '''
    device_address = '00'
    global_address = 99
    global_address_wo_response = 98
#    _terminator = chr(13)

    emissivity = Property(Float(enter_set=True, auto_set=False), depends_on='_emissivity')
    _emissivity = Float(50.0)
    emmin = Float(10.0)
    emmax = Float(100.0)
    pointer = Button
    pointing = Bool
    pointer_label = Property(depends_on='pointing')

    units = Str('C')
    temperature = Float

    char_write = True
    scan_func = 'read_temperature'

#    def __init__(self, *args, **kw):
#        '''
#
#        '''
#        super(MikronGA140Pyrometer, self).__init__(*args, **kw)
#        self.emmin = 10
#        self.emmax = 100
#
#    def _scan_(self):
#        '''
#        '''
#        func = getattr(self, self.scan_func)
#        func()
#
#    def emissivity_scan(self):
#        '''
#        '''
#        self.stream_manager.record(self.emissivity, self.name)

    def initialize(self, *args, **kw):
        '''
        '''

        self.read_emissivity()
        return True

    def load_additional_args(self, config):
        '''

        '''
        self._communicator.char_write = True
        return True

    def _build_command(self, cmd, value=None, per_mil=False, single_digit=False):
        '''

        '''
        fmt = '{}{}' if value is None else '{}{}{:04n}' if per_mil else \
            '{}{}{:n}' if single_digit else '{}{}{:02n}'
        args = (self.device_address, cmd)

        if value is not None:
            args += (int(value),)

        return fmt.format(*args)

    def _parse_response(self, resp, scalar=10, response_type='float'):
        '''

        '''
        if resp is None:
            if response_type == 'float':
                resp = self.get_random_value()
        else:

            resp = resp.strip()
            if response_type == 'float':
                try:
                        resp = int(resp)
                except:
                    resp = 0
                resp /= float(scalar)
            elif response_type == 'hex_range':
                    low = int(resp[:4], 16)
                    high = int(resp[4:], 16)
                    resp = (low, high)
        return resp

    def read_temperature(self, **kw):
        '''
        '''

        cmd = self._build_command('ms')
        temp = self._parse_response(self.ask(cmd, **kw))

        self.temperature = temp if temp is not None else 0.0

        return self.temperature

    def read_basic_temperature_range(self):
        '''
        '''
        cmd = self._build_command('mb')
        return self._parse_response(self.ask(cmd), response_type='hex_range')

    def read_emissivity(self):
        '''
        '''
        cmd = self._build_command('em')
        emv = self._parse_response(self.ask(cmd), scalar=10)
        if emv and not self.simulation:
            self._emissivity = emv
            # self.trait_property_changed('emissivity', emv)
        return emv

    def read_internal_temperature(self):
        '''
        '''
        cmd = self._build_command('gt')
        return self._parse_response(self.ask(cmd))

    def set_exposition_time(self, value):
        '''
            0 = intrinsic time constant of the device
            1 = 0.01 s    4 = 1.00 s    2 = 0.05 s
            5 = 3.00 s    3 = 0.25 s    6 = 10.00 s
        '''
        cmd = self._build_command('ez', value=value, single_digit=True)
        self.ask(cmd)

    def _get_emissivity(self):
        '''
        '''
        return self._emissivity

    def _set_emissivity(self, v):
        '''

        '''
        v = min(max(v, self.emmin), self.emmax)

        if v != self._emissivity:

            self.set_emissivity(v)
#            if resp is not None or resp is not 'no':
#                self._emissivity = v

    def _validate_emissivity(self, v):
        '''

        '''
        try:
            return float(v)
        except:
            pass

    def set_emissivity(self, emv, per_mil=True):
        '''
            set emissivity in %
        '''

        v = emv * 10.0 if per_mil else emv
        cmd = self._build_command('em', value=v, per_mil=per_mil)

        resp = self._parse_response(self.ask(cmd), response_type='text')
        if resp is not None or self.simulation:
            self._emissivity = emv

    def set_analog_output(self, output_range_id):
        '''
            0 = 0...20mA  1 = 4...20mA
        '''
        cmd = self._build_command('as',
                                value=output_range_id,
                                single_digit=True
                                )
        self.ask(cmd)

    def _get_pointer_label(self):
        '''
        '''
        return 'Pointer ON' if not self.pointing else 'Pointer OFF'

    def _pointer_fired(self):
        '''
        '''
        self.pointing = not self.pointing

        self.set_laser_pointer(self.pointing)

    def set_laser_pointer(self, onoff):
        '''
        True = on
        False = off
        '''
        value = 1 if onoff else 0

        cmd = self._build_command('la', value=value, single_digit=True)
        return self.ask(cmd)

    def get_control_group(self):
        cg = Group(HGroup(Item('pointer', editor=ButtonEditor(label_value='pointer_label')),
                          spring,
                          show_labels=False),
                  Item('temperature', style='readonly'),
                  Item('emissivity', editor=RangeEditor(format='%0.1f',
                                                        mode='slider',
                                                         low_name='emmin',
                                                         high_name='emmax'
                                                         )))
        return cg

#============= EOF =============================================

#    def scan(self, *args):
#        '''
#
#        '''
#
#        if super(MikronGA140Pyrometer, self).scan(*args) is None:
#            self.current_value = v = self.read_temperature()
#            self.stream_manager.record(v, self.name)
#    def traits_view(self):
#        '''
#        '''
#
#        return View(self.get_control_group())
