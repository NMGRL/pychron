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



'''
Vue Metrix Vue-TEC controller 
see http://www.vuemetrix.com/support/tech/tec_commands.html
'''
# =============enthought library imports=======================
from traits.api import Float
from traitsui.api import VGroup, Item
# =============standard library imports ========================
# import os
# =============local library imports  =========================
from pychron.hardware.core.core_device import CoreDevice


class VueDiodeControlModule(CoreDevice):
    """
    """
    thermistor_slope = -38.89
    thermistor_intercept = 73.97

    laser_amps = Float(12)
    laser_temperature = Float(34)
    laser_power = Float
    laser_voltage = Float
    scan_func = 'update'

    def initialize(self, *args, **kw):
        """
        """
        self.get_fault_flags()
        self.clear_fault_flags()
        return True

    #    def _scan_(self, *args, **kw):
    #        '''
    #            @type *args: C{str}
    #            @param *args:
    #
    #            @type **kw: C{str}
    #            @param **kw:
    #        '''
    #        r = self.get_laser_power(verbose = False)
    #
    #        self.stream_manager.record(r, self.name)
    def get_internal_temperature(self, **kw):
        """
        """
        t = self.read_laser_temperature_adc(**kw)
        if t is None:
            t = self.get_random_value(0, 50)
        else:
            t = self.thermistor_intercept + 2.5 * t / 4096. * self.thermistor_slope
        # convert to temperature scale
        return t

    def get_current(self):
        return self.read_laser_current_adc()

    def get_power(self):
        return self.read_laser_power_adc()

    def get_voltage(self):
        return self.read_laser_voltage_adc()

    def clear_fault_flags(self, **kw):
        """
        """
        cmd = 'cf'
        res = self.ask(cmd, **kw)

        return self._parse_response(res)

    def enable(self, **kw):
        """
        """
        if self.simulation:
            return True

        self.get_fault_flags()
        if self.clear_fault_flags():
            cmd = 'l1'
            self.start_scan()
            return self._parse_response(self.ask(cmd, **kw))

    def disable(self, **kw):
        """
        """
        self.stop_scan()
        cmd = 'l0'
        self.ask(cmd, **kw)

    def get_fault_flags(self, **kw):
        """
        """
        cmd = 'f?'
        return self.ask(cmd, **kw)

    def read_measured_power(self, **kw):
        """
        """
        cmd = 'pa?'
        return self._parse_response(self.ask(cmd, **kw), type_='float')


    def read_adc(self, _id, **kw):
        '''

            
        '''
        cmd = 'adi%i?' % _id
        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def read_laser_current_adc(self, **kw):
        """
        """
        cmd = 'adi?'
        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def read_laser_temperature_adc(self, **kw):
        """
        """
        cmd = 'adlt?'
        # cmd = 't0?'

        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def read_laser_power_adc(self, **kw):
        """
        """
        cmd = 'adp?'
        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def read_laser_voltage_adc(self, **kw):
        """
        """
        cmd = 'adv?'
        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def read_laser_amps(self, **kw):
        """
        """
        cmd = 'i?'
        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def read_external_control_adc(self, **kw):
        cmd = 'adixc?'
        return self._parse_response(self.ask(cmd, **kw), type_='float')

    def set_request_amps(self, a, **kw):
        """

        """
        cmd = 'i {:0.3d}'.format(a)
        self.ask(cmd, **kw)

    def _parse_response(self, res, type_='bool'):
        """
        """
        r = None
        if res is not None:  # and res is not 'simulation':
            res = res.strip()
            if type_ == 'bool':
                if res == 'OK':
                    return True
            elif type_ == 'float':
                try:
                    r = float(res)
                except ValueError, e:
                    self.warning(e)
        else:
            if type_ == 'float':
                r = self.get_random_value(0, 100)

        return r

    def update(self, **kw):

        a = self.read_laser_amps(verbose=False)
        if a is not None:
            self.laser_amps = a

        t = self.get_internal_temperature(verbose=False)
        if t is not None:
            self.laser_temperature = t

        p = self.read_measured_power(verbose=False)
        if p is not None:
            self.laser_power = p

        v = self.read_laser_voltage_adc(verbose=False)
        if v is not None:
            self.laser_voltage = v

    def get_control_group(self):
        g = VGroup(
            Item('laser_amps', format_str='%0.2f', style='readonly'),
            Item('laser_temperature', format_str='%0.2f', style='readonly'),
            Item('laser_power', format_str='%0.2f', style='readonly'),
            Item('laser_voltage', format_str='%0.2f', style='readonly'))
        return g

# ============= EOF ====================================
