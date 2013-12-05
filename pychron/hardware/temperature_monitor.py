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
from traits.api import Float, Property, Str
from traitsui.api import Item, EnumEditor, VGroup
#=============standard library imports ========================
# import time
#=============local library imports  ==========================
from core.core_device import CoreDevice
from pychron.hardware.core.data_helper import make_bitarray
# from modbus.modbus_device import ModbusDevice
# class TemperatureMonitor(ModbusDevice, Streamable):
#    def initialize(self):
#        pass
#    def scan(self, *args):
#        '''
#
#        '''
#        if super(TemperatureMonitor, self).scan(*args) is None:
#            self.current_value = v = self.read_temperature(verbose = False)
#            self.stream_manager.record(v, self.name)
# from pychron.graph.time_series_graph import TimeSeriesStreamGraph


class ISeriesDevice(CoreDevice):
    '''
        http://www.omega.com/iseries/Pdf/M3397CO.pdf
    '''
    prefix = '*'
    scan_func = 'read_device'
    process_value = Float

    def _parse_response(self, re):
        '''
        '''
        if re is not None:
#            if re == 'simulation':
#                return self.get_random_value()

            args = re.split(' ')

            if len(args) > 1:
                try:
                    return float(args[1])
                except ValueError:
                    pass

            return re
#        else:
#            mi = -10
#            ma = 10
#            return self.get_random_value(min=mi, max=ma)

    def _build_command(self, cmd_type, cmd_indx):
        '''
        '''
        return '{}{}{}'.format(self.prefix, cmd_type, cmd_indx)

    def _write_command(self, commandindex, value=None):
        '''
        '''
        args = [self.prefix, 'W', commandindex]

        if value is not None:
            args += [str(value)]
        self.ask(''.join(args),
                 # delay = 400
                 )


INPUT_CLASS_MAP = {0: 'TC', 1: 'RTD', 2: 'PROCESS'}
TC_MAP = {0: 'J', 1: 'K', 2: 'T', 3: 'E', 4: 'N', 5: 'Din-J', 6: 'R', 7: 'S', 8: 'B', 110: 'C'}
TC_KEYS = ['J', 'K', 'T', 'E', 'N', 'Din-J', 'R', 'S', 'B', 'C']


class DPi32TemperatureMonitor(ISeriesDevice):
    '''
    '''
    scan_func = 'read_temperature'
    input_type = Property(depends_on='_input_type')
    _input_type = Str
    id_query = '*R07'

    def id_response(self, response):
        r = False
        if response is not None:
            re = response.strip()
            # strip off first three command characters
            if re[:3] == 'R07':
                r = True

        return r

    def initialize(self, *args, **kw):
        #self.set_input_type('C')

        self.info('getting input type')
        return self.read_input_type()

    def _get_input_type(self):
        '''
        '''
        return self._input_type

    def _set_input_type(self, v):
        '''
        '''
        self._input_type = v
        self.set_input_type(v)

    def get_process_value(self):
        '''
        '''
        return self.process_value

    def read_temperature(self, **kw):
        '''
        '''
        commandindex = '01'
#        com = self._build_command('V', commandindex)
        com = ('V', commandindex)
#        kw.update(verbose=False)
        x = self.repeat_command(com, check_type=float, **kw)
        if x is not None:
            self.process_value = x
            return x

    def set_busformat(self):
        commandindex = '1F'

        sep = 0  # space
        flow = 0  # continoues
        mode = 0  # rs232
        echo = 1  # echo
        linefeed = 1
        modbus = 0

        bits = '00{}{}{}{}{}{}'.format(sep,
                                       flow,
                                       mode,
                                       echo,
                                       linefeed,
                                       modbus
                                       )
        value = '{:02X}'.format(int(bits, 2))
        self._write_command(commandindex, value)

    def set_input_type(self, v):
        '''
        '''
        commandindex = '07'

        input_class = '00'

        # bits 7,6 meaningless for thermocouple
        bits = '00{}{}'.format(make_bitarray(TC_KEYS.index(v),
                                                  width=4),
                                input_class
                                )
        value = '{:02X}'.format(int(bits, 2))

        self._write_command(commandindex, value=value)

    def read_input_type(self):
        '''
        '''
#        commandindex = '07'
#        com = self._build_command('R', commandindex)

#        re = self.ask(com)

        cmd = 'R', '07'
        re = self.repeat_command(cmd)
        if re is not None:
            re = re.strip()
            # strip off first three command characters
            # compare with sent command for error checking
            if re[:3] == 'R07':
                re = make_bitarray(int(re[3:]))
                input_class = INPUT_CLASS_MAP[int(re[:2], 2)]
                if input_class == 'TC':
                    self._input_type = TC_MAP[int(re[2:6], 2)]

                return True

    def reset(self):
        '''
        '''
        c = self._build_command('Z', '02')
        self.ask(c)

    def graph_builder(self, g):
        g.new_plot(
                   padding=[20, 5, 5, 20],
                   scan_delay=self.scan_period * self.time_dict[self.scan_units] / 1000.0,
                   zoom=True,
                   pan=True,
                   )
        g.new_series()

    def get_control_group(self):
        return VGroup(Item('process_value', style='readonly'),
                    Item('input_type', editor=EnumEditor(values=TC_KEYS), show_label=False))

#    def current_state_view(self):
#        v = super(DPi32TemperatureMonitor, self).current_state_view()
#
#        v.content.content.append(VGroup(Item('graph', show_label=False, style='custom'),
#                                        Item('scan_func', label='Function', style='readonly'),
#                                        Item('scan_period', label='Period ({})'.format(self.scan_units), style='readonly'),
#                                        label='Scan'
#                                        )
#                                 )
#        return v
#============= EOF ============================================
