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

#=============enthought library imports========================
import os
from traits.api import Enum, Float, Event, Property, Int, Button, Bool, Str, Any, on_trait_change, String
from traitsui.api import View, HGroup, Item, Group, VGroup, EnumEditor, RangeEditor, ButtonEditor, spring
# from pyface.timer.api import Timer

#=============standard library imports ========================
# import sys, os
#=============local library imports  ==========================
# sys.path.insert(0, os.path.join(os.path.expanduser('~'),
#                               'Programming', 'mercurial', 'pychron_beta'))

from core.core_device import CoreDevice
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph

from pychron.graph.plot_record import PlotRecord
import time
from pychron.hardware.meter_calibration import MeterCalibration
from pychron.core.helpers.filetools import parse_file

sensor_map = {'62': 'off',
              '95': 'thermocouple',
              '104': 'volts dc',
              '112': 'milliamps',
              '113': 'rtd 100 ohm',
              '114': 'rtd 1000 ohm',
              '155': 'potentiometer',
              '229': 'thermistor'}

isensor_map = {'off': 62,
               'thermocouple': 95,
               'volts dc': 104,
               'milliamps': 112,
               'rtd 100 ohm': 113,
               'rtd 1000 ohm': 114,
               'potentiometer': 155,
               'thermistor': 229}

itc_map = {'B': 11, 'K': 48,
           'C': 15, 'N': 58,
           'D': 23, 'R': 80,
           'E': 26, 'S': 84,
           'F': 30, 'T': 93,
           'J': 46, }

tc_map = {'11': 'B', '48': 'K',
          '15': 'C', '58': 'N',
          '23': 'D', '80': 'R',
          '26': 'E', '84': 'S',
          '30': 'F', '93': 'T',
          '46': 'J'}
autotune_aggressive_map = {'under': 99,
                           'critical': 21,
                           'over': 69}

yesno_map = {'59': 'NO', '106': 'YES'}
truefalse_map = {'59': False, '106': True}
heat_algorithm_map = {'62': 'off', '71': 'PID', '64': 'on-off'}
baudmap = {'9600': 188, '19200': 189, '38400': 190}
ibaudmap = {'188': '9600', '189': '19200', '190': '38400'}


class WatlowEZZone(CoreDevice):
    """
        WatlowEZZone represents a WatlowEZZone PM PID controller.
        this class provides human readable methods for setting the modbus registers
    """

    graph_klass = TimeSeriesStreamStackedGraph
    refresh = Button
    Ph = Property(Float(enter_set=True,
                        auto_set=False), depends_on='_Ph_')
    _Ph_ = Float(50)
    Pc = Property(Float(enter_set=True,
                        auto_set=False), depends_on='_Pc_')
    _Pc_ = Float(4)
    I = Property(Float(enter_set=True,
                       auto_set=False), depends_on='_I_')
    _I_ = Float(32)
    D = Property(Float(enter_set=True,
                       auto_set=False), depends_on='_D_')
    _D_ = Float(33)

    dead_band = Property(Float(enter_set=True,
                               auto_set=False), depends_on='_dead_band')
    _dead_band = Float

    stablization_time = Float(3.0)
    sample_time = Float(0.25)
    nsamples = Int(5)
    tune_setpoint = Float(500.0)
    delay = Int(1)

    closed_loop_setpoint = Property(Float(0,
                                          auto_set=False,
                                          enter_set=True),
                                    depends_on='_clsetpoint')
    calibrated_setpoint = Float

    _clsetpoint = Float(0.0)
    setpointmin = Float(0.0)
    setpointmax = Float(100.0)

    open_loop_setpoint = Property(Float(0, auto_set=False,
                                        enter_set=True),
                                  depends_on='_olsetpoint')
    _olsetpoint = Float(0.0)
    olsmin = Float(0.0)
    olsmax = Float(100.0)

    max_output = Property(Float(enter_set=True, auto_set=False),
                          depends_on='_max_output')
    _max_output = Float(100)

    input_scale_low = Property(Float(auto_set=False, enter_set=True),
                               depends_on='_input_scale_low')
    _input_scale_low = Float(0)

    input_scale_high = Property(Float(auto_set=False, enter_set=True),
                                depends_on='_input_scale_high')
    _input_scale_high = Float(1)

    output_scale_low = Property(Float(auto_set=False, enter_set=True),
                                depends_on='_output_scale_low')
    _output_scale_low = Float(0)

    output_scale_high = Property(Float(auto_set=False, enter_set=True),
                                 depends_on='_output_scale_high')
    _output_scale_high = Float(1)

    control_mode = Property(depends_on='_control_mode')
    _control_mode = String('closed')

    autotune = Event
    autotune_label = Property(depends_on='autotuning')
    autotuning = Bool

    autotuning_additional_recording = 15
    acount = 0

    configure = Button

    autotune_setpoint = Property(Float(auto_set=False, enter_set=True),
                                 depends_on='_autotune_setpoint')
    _autotune_setpoint = Float(0)

    autotune_aggressiveness = Property(Enum('under', 'critical', 'over'),
                                       depends_on='_autotune_aggressiveness')
    _autotune_aggressiveness = Str

    enable_tru_tune = Property(Bool,
                               depends_on='_enable_tru_tune')
    _enable_tru_tune = Bool

    tru_tune_band = Property(Int(auto_set=False, enter_set=True),
                             depends_on='_tru_tune_band')
    _tru_tune_band = Int(0)

    tru_tune_gain = Property(Enum(('1', '2', '3', '4', '5', '6')),
                             depends_on='_tru_tune_gain')
    _tru_tune_gain = Str

    heat_algorithm = Property(Enum('PID', 'On-Off', 'Off'),
                              depends_on='_heat_algorithm')
    _heat_algorithm = Str

    sensor1_type = Property(Enum('off', 'thermocouple', 'volts dc',
                                 'milliamps', 'rtd 100 ohm', 'rtd 1000 ohm', 'potentiometer', 'thermistor'),
                            depends_on='_sensor1_type')

    thermocouple1_type = Property(Enum('B', 'K',
                                       'C', 'N',
                                       'D', 'R',
                                       'E', 'S',
                                       'F', 'T',
                                       'J'),
                                  depends_on='_thermocouple1_type')

    _sensor1_type = Int
    _thermocouple1_type = Int

    process_value = Float

    heat_power_value = Float
    # scan_func = 'get_temperature'
    scan_func = 'get_temp_and_power'

    memory_blocks_enabled = Bool(True)
    program_memory_blocks = Bool(True)

    _process_working_address = 200
    _process_memory_block = [360, 1904]
    _process_memory_len = 4

    calibration = Any
    use_calibrated_temperature = Bool(False)
    coeff_string = Property

    use_pid_bin = Bool(True)
    default_output=Int(1)
    advanced_values_button=Button
    min_output_scale=Float
    max_output_scale=Float

    #def _get_use_calibrated_temperature(self):
    #    return self._use_calibrated_temperature and self.calibration is not None

    #def _set_use_calibrated_temperature(self, v):
    #    self._use_calibrated_temperature = v
    # reciprocal_power=Bool(True)

    def _get_coeff_string(self):
        s = ''
        if self.calibration:
            s = self.calibration.coeff_string
        return s

    def _set_coeff_string(self, v):
        cal = self.calibration
        if cal is None:
            cal = MeterCalibration()
            self.calibration = cal

        cal.coeff_string = v

    @on_trait_change('calibration:coefficients')
    def _coeff_string_changed(self):

        config = self.get_configuration()
        if not config.has_section('Calibration'):
            config.add_section('Calibration')

        config.set('Calibration', 'coefficients', self.calibration.dump_coeffs())
        with open(self.config_path, 'w') as fp:
            config.write(fp)

    def map_temperature(self, te, verbose=True):
        if self.use_calibrated_temperature:
            if self.calibration:
                if verbose:
                    self.info(
                        'using temperature coefficients  (e.g. ax2+bx+c) {}'.format(self.calibration.print_string()))
                if abs(te) < 1e-5:
                    te = 0
                else:
                    te = min(max(0, self.calibration.get_input(te)), self.setpointmax)

            else:
                self.info('no calibration set')

        return te

    def initialize(self, *args, **kw):
        if self.read_baudrate(port=1):
            # set open loop and closed loop to zero
            self.disable()
            if self.program_memory_blocks:
                self._program_memory_blocks()

            # p = self.read_high_power_scale()
            # p=self.read_out
            # if p:
            #     self._max_output = p

            self.initialization_hook()

            self._load_max_output()

            self.setup_consumer()

            return True
        else:
            self.warning('Failed connecting to Temperature Controller')

    def is_programmed(self):
        r = self.get_temp_and_power()
        if r is not None:
            return r.data[0] > 1

    def _load_max_output(self):
        oh = self.output_scale_high
        ol = self.output_scale_low

        mo = self.max_output_scale
        mi = self.min_output_scale
        # print oh, ol, mo, mi
        self._max_output = (oh - ol) / (mo - mi)*100

    def _program_memory_blocks(self):
        """
            see watlow ez zone pm communications rev b nov 07
            page 5
            User programmable memory blocks
        """
        self._process_memory_len = 0
        self.info('programming memory block')
        for i, ta in enumerate(self._process_memory_block):
            self.set_assembly_definition_address(self._process_working_address + 2 * i, ta)
            self._process_memory_len += 2

    def report_pid(self):
        pid_attrs = ['_Ph_', '_Pc_', '_I_', '_D_']
        self.info('read pid parameters')
        pid_vals = self.read(1890, nregisters=8, nbytes=21, response_type='float')
        if pid_vals:
            self.info('======================== PID =====================')
            for pa, pv in zip(pid_attrs, pid_vals):
                setattr(self, pa, pv)
                self.info('{} set to {}'.format(pa, pv))
            self.info('==================================================')
        return pid_vals

    def initialization_hook(self):
        self.info('read input sensor type')
        s = self.read_analog_input_sensor_type(1)
        if s is not None:
            self._sensor1_type = s

        if self._sensor1_type == 95:
            t = self.read_thermocouple_type(1)
            if t is not None:
                self._thermocouple1_type = t

        self.report_pid()

        self.info('read input/output scaling')
        if not self.simulation:
            try:
                osl, osh = self.read(736, nregisters=4, nbytes=13)
                isl, ish = self.read(388, nregisters=4, nbytes=13)

                self._output_scale_low = osl
                self._output_scale_high = osh
                self._input_scale_low = isl
                self._input_scale_high = ish
            except TypeError:
                pass

        attrs = [
            ('read_autotune_setpoint', '_autotune_setpoint'),
            ('read_autotune_aggressiveness', '_autotune_aggressiveness'),
            ('read_tru_tune_enabled', '_enable_tru_tune'),
            ('read_tru_tune_band', '_tru_tune_band'),
            ('read_tru_tune_gain', '_tru_tune_gain'),

            #               ('read_output_scale_low', '_output_scale_low'),
            #               ('read_output_scale_high', '_output_scale_high'),
            #               ('read_input_scale_low', '_input_scale_low'),
            #               ('read_input_scale_high', '_input_scale_high'),

            ('read_control_mode', '_control_mode')
        ]
        for func, attr in attrs:
            v = getattr(self, func)()
            if v is not None:
                setattr(self, attr, v)

    def get_temp_and_power(self, verbose=False, **kw):
    #        if 'verbose' in kw and kw['verbose']:
    #            self.info('Read temperature and heat power')

    #        kww = kw.copy()
    #        kww['verbose'] = False
        if self.memory_blocks_enabled:
            args = self.read(self._process_working_address,
                             nbytes=13,
                             nregisters=self._process_memory_len, verbose=verbose, **kw)

            if not args or not isinstance(args, (tuple, list)):
                args = None, None

            t, p = args

        else:
            t = self.read_process_value(1, **kw)
            p = self.read_heat_power(**kw)

        #        print self.simulation
        if self.simulation:
        #            t = 4 + self.closed_loop_setpoint
            t = self.get_random_value() + self.closed_loop_setpoint
            p = self.get_random_value()

        t = self.process_value if t is None else min(t, 2000)
        p = self.heat_power_value if p is None else max(0, min(p, 100))

        self.trait_set(process_value=t, heat_power_value=p)
        if 'verbose' in kw and kw['verbose']:
            self.info('Temperature= {} Power= {}'.format(t, p))

        return PlotRecord([t, p], (0, 1), ('Temp', 'Power'))

    def get_temperature(self, **kw):
        if 'verbose' in kw and kw['verbose']:
            self.info('Read temperature')

        t = None
        if self.simulation:
        #            t = 4 + self.closed_loop_setpoint
            t = self.get_random_value() + self.closed_loop_setpoint
        else:
            if self.memory_blocks_enabled:
                args = self.read(self._process_working_address,
                                 nbytes=13,
                                 nregisters=self._process_memory_len, **kw)
                if args:
                    t, _ = args
                    #                if not args or not isinstance(args, (tuple, list)):
                    #                    args = None, None
                    #
                    #                t, _ = args

                    #            t = self.read_process_value(1, **kw)
                    # print t
        if t is not None:
            try:

                t = float(t)
                self.process_value = t
                #                self.process_value_flag = True
                return t
            except (ValueError, TypeError), e:
                print 'watlow gettemperature', e

    def disable(self):
        self.info('disable')

        func = getattr(self, 'set_{}_loop_setpoint'.format(self.control_mode))
        func(0)

    #        self.set_control_mode('open')
    #        self.set_open_loop_setpoint(0)

    def load_additional_args(self, config):
        """
        """
        self.set_attribute(config, 'min_output_scale', 'Output', 'scale_low', cast='float')
        self.set_attribute(config, 'max_output_scale', 'Output', 'scale_high', cast='float')

        self.set_attribute(config, 'setpointmin', 'Setpoint', 'min', cast='float')
        self.set_attribute(config, 'setpointmax', 'Setpoint', 'max', cast='float')

        self.set_attribute(config, 'memory_blocks_enabled', 'MemoryBlock', 'enabled', cast='boolean')
        if self.memory_blocks_enabled:
            self.set_attribute(config, 'program_memory_blocks', 'MemoryBlock', 'program', cast='boolean')
            #            if self.program_memory_blocks:
        #                self.memory_blocks=[]
        #                for option in config.options('MemoryBlock'):
        #                    if option.startswith('block'):
        #                        self.memory_blocks.append(config.get('MemoryBlock',option))

        coeffs = self.config_get(config, 'Calibration', 'coefficients')
        if coeffs:
            self.calibration = MeterCalibration(coeffs)
            #self.use_calibrated_temperature = True
        return True

    def set_nonvolatile_save(self, yesno, **kw):

        v = 106 if yesno else 59
        self.write(2494, v, **kw)

    def read_nonvolative_save(self):
        r = self.read(2494, response_type='int')
        print 'nonvolative save', r

    def set_assembly_definition_address(self, working_address, target_address, **kw):
        ada = working_address - 160

        self.info('setting {} to {}'.format(ada, target_address))
        #        self.write(ada, target_address, nregisters=2, **kw)

        self.write(ada, (target_address, target_address + 1), nregisters=2, **kw)
        #        self.info('setting {} to {}'.format(ada, target_address))
        check = False
        if check:
            r = self.read(ada, response_type='int')
            self.info('register {} pointing to {}'.format(ada, r))
            r = self.read(ada + 1, response_type='int')
            self.info('register {} pointing to {}'.format(ada + 1, r))

    def read_baudrate(self, port=1):
        """
            com port 2 is the modbus port
        """
        register = 2484 if port == 1 else 2504
        r = self.read(register, response_type='int')
        if r:
            try:
                return ibaudmap[str(r)]
            except KeyError, e:
                self.debug('read_baudrate keyerror {}'.format(e))

    def set_baudrate(self, v, port=1):
        """
            com port 2 is the modbus port
        """
        register = 2484 if port == 1 else 2504

        try:
            value = baudmap[v]
            self.write(register, value)

        except KeyError, e:
            self.debug('set_baudrate keyerror {}'.format(e))

    def set_closed_loop_setpoint(self, setpoint, set_pid=True, **kw):
        self._clsetpoint = setpoint
        if self.use_calibrated_temperature and self.calibration:
            setpoint = self.map_temperature(setpoint)

        if set_pid:
            self.set_pid(setpoint)

        self.calibrated_setpoint = setpoint
        self.info('setting closed loop setpoint = {:0.3f}'.format(setpoint))

        self.write(2160, setpoint, nregisters=2, **kw)
        #        time.sleep(0.025)
        sp = self.read_closed_loop_setpoint()
        try:
            e = abs(sp - setpoint) > 0.01
        except Exception, _ee:
            e = True

        time.sleep(0.025)
        if sp and e:
            self.warning('Set point not set. {} != {} retrying'.format(sp, setpoint))
            self.write(2160, setpoint, nregisters=2, **kw)

    def set_open_loop_setpoint(self, setpoint, use_calibration=None, verbose=True, set_pid=False, **kw):
        if verbose:
            self.info('setting open loop setpoint = {:0.3f}'.format(setpoint))
        self._olsetpoint = setpoint

        self.write(2162, setpoint, nregisters=2, verbose=verbose, **kw)

    def set_temperature_units(self, comms, units, **kw):
        register = 2490 if comms == 1 else 2510
        value = 15 if units == 'C' else 30
        self.write(register, value)

    def set_calibration_offset(self, input_id, value, **kw):
        self.info('set calibration offset {}'.format(value))
        register = 382 if input_id == 1 else 462
        self.write(register, value, nregisters=2, **kw)

    def set_control_mode(self, mode, **kw):
        """
            10=closed
            54=open
        """
        if mode=='open':
            self.output_scale_low=self.min_output_scale
            self.output_scale_high=self.max_output_scale

        self.info('setting control mode = %s' % mode)
        self._control_mode = mode
        value = 10 if mode == 'closed' else 54
        self.write(1880, value, **kw)

    #===============================================================================
    # Autotune
    #===============================================================================
    def autotune_finished(self, verbose=False, **kw):
        r = self.read(1920, response_type='int', verbose=verbose, **kw)
        try:
            return not truefalse_map[str(r)]
        except KeyError:
            return True

    def start_autotune(self, **kw):
        self.info('start autotune')
        self.write(1920, 106, **kw)

    def stop_autotune(self, **kw):
        """
        """
        self.info('stop autotune')
        self.write(1920, 59, **kw)

    def set_autotune_setpoint(self, value, **kw):
        """
            Set the set point that the autotune will use,
            as a percentage of the current set point.
        """
        self.info('setting autotune setpoint {:0.3f}'.format(value))
        self.write(1998, value, nregisters=2, **kw)

    def set_autotune_aggressiveness(self, key, **kw):
        """
            under damp - reach setpoint quickly
            critical damp - balance a rapid response with minimal overshoot
            over damp - reach setpoint with minimal overshoot
        """
        key = key.lower()
        if key in autotune_aggressive_map:
            value = autotune_aggressive_map[key]

            self.info('setting auto aggressiveness {} ({})'.format(key, value))

            self.write(1916, value, **kw)

    def set_tru_tune(self, onoff, **kw):
        if onoff:
            msg = 'enable TRU-TUNE+'
            value = 106
        else:
            msg = 'disable TRU-TUNE+'
            value = 59
        self.info(msg)
        self.write(1910, value, **kw)

    def set_tru_tune_band(self, value, **kw):
        """
            0 -100 int
            
            only adjust this parameter is controller is unable to stabilize.
            only the case for processes with fast responses
            
        """
        self.info('setting TRU-TUNE+ band {}'.format(value))
        self.write(1912, int(value), **kw)

    def set_tru_tune_gain(self, value, **kw):
        """
            1-6 int
            1= most aggressive response and potential for overshoot
            6=least "                                      "
        """
        self.info('setting TRU-TUNE+ gain {}'.format(value))
        self.write(1914, int(value), **kw)

    #===============================================================================
    #  PID
    #===============================================================================
    def set_pid(self, temp):
        """
            get pids from config
            find bin ``temp`` belongs to and get pid
            set temperature controllers pid
        """
        if self.use_pid_bin:
            pid_bin = self._get_pid_bin(temp)
            self.debug('pid bin for {}. {}'.format(temp, pid_bin))
            if pid_bin:
                self.trait_set(Ph=pid_bin[0], I=pid_bin[2], D=pid_bin[3])
                if len(pid_bin)==5:
                    self.max_output=pid_bin[4]
                else:
                    self.max_output=100

    def set_heat_algorithm(self, value, **kw):
        self.info('setting heat algorithm {}'.format(value))
        self.write(1890)

    def set_heat_proportional_band(self, value, **kw):
        self.info('setting heat proportional band ={:0.3f}'.format(value))
        self.write(1890, value, nregisters=2, **kw)

    def set_cool_proportional_band(self, value, **kw):
        self.info('setting cool proportional band = {:0.3f}'.format(value))
        self.write(1892, value, nregisters=2, **kw)

    def set_time_integral(self, value, **kw):
        self.info('setting time integral = {:0.3f}'.format(value))
        self.write(1894, value, nregisters=2, **kw)

    def set_time_derivative(self, value, **kw):
        self.info('setting time derivative = {:0.3f}'.format(value))
        self.write(1896, value, nregisters=2, **kw)

    def set_dead_band(self, v, **kw):
        """
            Set the offset to the proportional band. With
            a negative value, both heating and cooling outputs are active
            when the process value is near the set point. 
            A positive value keeps heating and cooling outputs from fighting each other.
        """
        self.info('setting dead_band = {:0.3f}'.format(v))
        register = 1898
        self.write(register, v, nregisters=2, **kw)

    #===============================================================================
    # Output
    #===============================================================================
    def set_output_function(self, value, **kw):
        inmap = {'heat': 36,
                 'off': 62}
        if value in inmap:
            self.info('set output function {}'.format(value))
            value = inmap[value]
            self.write(722, value, **kw)

    def set_input_scale_low(self, value, **kw):
        self.info('set input scale low {}'.format(value))
        self.write(338, value, nregisters=2, **kw)

    def set_input_scale_high(self, value, **kw):
        self.info('set input scale high {}'.format(value))
        self.write(390, value, nregisters=2, **kw)

    def set_output_scale_low(self, value, **kw):
        self.info('set output scale low {}'.format(value))
        self.write(736, value, nregisters=2, **kw)

    def set_output_scale_high(self, value, **kw):
        self.info('set output scale high {}'.format(value))
        self.write(738, value, nregisters=2, **kw)

    def set_analog_input_sensor_type(self, input_id, value, **kw):
        self.info('set input sensor type {}'.format(value))
        register = 368 if input_id == 1 else 448
        v = value if isinstance(value, int) else isensor_map[value]
        self.write(register, v, **kw)
        if v == 95:
            tc = self.read_thermocouple_type(1)
            self._thermocouple1_type = tc

    def set_thermocouple_type(self, input_id, value, **kw):
        """
        """
        self.info('set input thermocouple type {}'.format(value))
        register = 370 if input_id == 1 else 450
        v = value if isinstance(value, int) else itc_map[value.upper()]

        self.write(register, v, **kw)

    def set_high_power_scale(self, value, output=None, **kw):
        if output is None:
            output=self.default_output

        self.info('set high power scale {}'.format(value))
        # register = 898 if output == 1 else 928
        register = 746 if output == 1 else 866
        # register= 898 if output ==1 else 898
        v = max(0, min(100, value))
        self.write(register, v, nregisters=2, **kw)

    #===============================================================================
    # readers
    #===============================================================================
    def read_output_state(self, **kw):
        rid = str(self.read(1012, response_type='int', **kw))
        units_map = {'63': 'On', '62': 'Off'}
        return units_map[rid] if rid in units_map else None

    def read_heat_proportional_band(self, **kw):
        return self.read(1890, nregisters=2, **kw)

    def read_cool_proportional_band(self, **kw):
        return self.read(1892, nregisters=2, **kw)

    def read_time_integral(self, **kw):
        return self.read(1894, nregisters=2, **kw)

    def read_time_derivative(self, **kw):
        return self.read(1896, nregisters=2, **kw)

    def read_calibration_offset(self, input_id, **kw):
        register = 382 if input_id == 1 else 462

        return self.read(register, nregisters=2, **kw)

    def read_closed_loop_setpoint(self, **kw):
        self.debug('read closed loop setpoint')
        return self.read(2160, nregisters=2, nbytes=9, **kw)

    def read_open_loop_setpoint(self, **kw):
        self.debug('read open loop setpoint')
        return self.read(2162, nregisters=2, **kw)

    def read_analog_input_sensor_type(self, input_id, **kw):
        if input_id == 1:
            register = 368
        else:
            register = 448

        return self.read(register, response_type='int', **kw)

    def read_thermocouple_type(self, input_id, **kw):
        if input_id == 1:
            register = 370
        else:
            register = 450
        rid = self.read(register, response_type='int', **kw)
        return rid

    def read_filtered_process_value(self, input_id, **kw):
        return self.read(402, nregisters=2, **kw)

    def read_process_value(self, input_id, **kw):
        """
            unfiltered process value
        """
        register = 360 if input_id == 1 else 440

        return self.read(register, nregisters=2, **kw)

    def read_error_status(self, input_id, **kw):
        register = 362 if input_id == 1 else 442
        return self.read(register, response_type='int', **kw)

    def read_temperature_units(self, comms):
        register = 2490 if comms == 1 else 2510
        rid = str(self.read(register, response_type='int'))
        units_map = {'15': 'C', '30': 'F'}
        return units_map[rid] if rid in units_map else None

    def read_control_mode(self, **kw):
        rid = self.read(1880, response_type='int', **kw)
        return 'closed' if rid == 10 else 'open'

    def read_heat_algorithm(self, **kw):
        rid = str(self.read(1884, response_type='int', **kw))
        return heat_algorithm_map[rid] if rid in heat_algorithm_map else None

    def read_open_loop_detect_enable(self, **kw):
        rid = str(self.read(1922, response_type='int'))
        return yesno_map[id] if rid in yesno_map else None

    def read_output_scale_low(self, **kw):
        return self.read(736, nregisters=2, **kw)

    def read_output_scale_high(self, **kw):
        return self.read(738, nregisters=2, **kw)

    def read_input_scale_low(self, **kw):
        return self.read(388, nregisters=2, **kw)

    def read_input_scale_high(self, **kw):
        return self.read(390, nregisters=2, **kw)

    def read_output_type(self, **kw):
        r_map = {'104': 'volts', '112': 'milliamps'}
        rid = str(self.read(720, response_type='int', **kw))
        return r_map[rid] if rid in r_map else None

    def read_output_function(self, **kw):
        rid = str(self.read(722, response_type='int', **kw))
        r_map = {'36': 'heat', '62': 'off'}

        return r_map[rid] if rid in r_map else None

    def read_heat_power(self, **kw):
        return self.read(1904, nregisters=2, **kw)

    def read_autotune_setpoint(self, **kw):
        self.debug('read autotune setpoint')
        #        r = self.read(1998, nregisters=2, **kw)
        r = self.read(1998, nregisters=2, nbytes=9, **kw)
        return r

    def read_autotune_aggressiveness(self, **kw):
        rid = str(self.read(1884, response_type='int', **kw))
        return heat_algorithm_map[rid] if rid in heat_algorithm_map else None

    def read_tru_tune_enabled(self, **kw):
        r = self.read(1910, response_type='int', **kw)
        r = str(r)

        try:
            return truefalse_map[r]
        except KeyError:
            pass

    def read_tru_tune_band(self, **kw):
        return self.read(1912, response_type='int', **kw)

    def read_tru_tune_gain(self, **kw):
        try:
            return str(self.read(1914, response_type='int', **kw))
        except ValueError:
            pass

    def read_high_power_scale(self, output=None, **kw):
        if output is None:
            output = self.default_output
        self.info('read high power scale {}'.format(output))
        register= 746 if output == 1 else 866
        # register = 898 if output == 1 else 898
        # register = 898 if output == 1 else 928
        # r = self.read(register, nregisters=2, nbytes=9, **kw)
        r = self.read(register, nregisters=2, nbytes=9, **kw)
        if self.reciprocal_power:
            r=100-r

        return r

    #    def read_cool_power(self,**kw):
    #        register=1906
    #        return self.read(register,**kw)
    #    def _scan_(self, *args, **kw):
    #        """
    #
    #        """
    #        p = self.get_temperature()
    #        record_id = self.name
    #        self.stream_manager.record(p, record_id)
    #===============================================================================
    # setters
    #===============================================================================
    def _set_sensor1_type(self, v):
        self._sensor1_type = isensor_map[v]
        self.set_analog_input_sensor_type(1, self._sensor1_type)

    def _set_thermocouple1_type(self, v):
        self._thermocouple1_type = itc_map[v]
        self.set_thermocouple_type(1, self._thermocouple1_type)

    def _set_closed_loop_setpoint(self, v):
    #         self.set_closed_loop_setpoint(v)
        self.add_consumable((self.set_closed_loop_setpoint, v))

    def _set_open_loop_setpoint(self, v):
        self.add_consumable((self.set_open_loop_setpoint, v))

    #         self.set_open_loop_setpoint(v)

    def _set_control_mode(self, mode):
        self.set_control_mode(mode)

    def _validate_Pc(self, v):
        if self._validate_number(v):
            return self._validate_new(v, self._Pc_)

    def _validate_Ph(self, v):
        if self._validate_number(v):
            return self._validate_new(v, self._Ph_)

    def _validate_I(self, v):
        if self._validate_number(v):
            return self._validate_new(v, self._I_)

    def _validate_D(self, v):
        if self._validate_number(v):
            return self._validate_new(v, self._D_)

    def _set_Ph(self, v):
        if v is not None:
            self._Ph_ = v
            self.set_heat_proportional_band(v)

    def _set_Pc(self, v):
        if v is not None:
            self._Pc_ = v
            self.set_cool_proportional_band(v)

    def _set_I(self, v):
        if v is not None:
            self._I_ = v
            self.set_time_integral(v)

    def _set_D(self, v):
        if v is not None:
            self._D_ = v
            self.set_time_derivative(v)

    def _set_calibration_offset(self, v):
        self._calibration_offset = v
        self.set_calibration_offset(1, v)

    def _set_input_scale_low(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._input_scale_low):
                self._input_scale_low = v
                self.set_input_scale_low(v)

    def _set_input_scale_high(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._input_scale_high):
                self._input_scale_high = v
                self.set_input_scale_high(v)

    def _set_output_scale_low(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._output_scale_low):
                self._output_scale_low = v
                self.set_output_scale_low(v)

    def _set_output_scale_high(self, v):
        """
        """
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._output_scale_high):
                self._output_scale_high = v
                self.set_output_scale_high(v)

    def _set_enable_tru_tune(self, v):

        self._enable_tru_tune = v
        self.set_tru_tune(v)

    def _set_tru_tune_band(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._tru_tune_band):
                self._tru_tune_band = v
                self.set_tru_tune_band(v)

    def _set_tru_tune_gain(self, v):
        self._tru_tune_gain = v
        self.set_tru_tune_gain(v)

    def _set_autotune_setpoint(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._autotune_setpoint):
                self._autotune_setpoint = v
                self.set_autotune_setpoint(v)

    def _set_autotune_aggressiveness(self, v):
        self._autotune_aggressiveness = v
        self.set_autotune_aggressiveness(v)

    def _set_heat_algorithm(self, v):
        self._heat_algorithm = v
        self.set_heat_algorithm(v)

    def _set_dead_band(self, v):
        self._dead_band = v
        self.set_dead_band(v)

    def _set_max_output(self, v):
        v=(self.max_output_scale-self.min_output_scale)*v/100.+self.output_scale_low
        self.output_scale_high=v
        # self.set_output_scale_high(v)
        self._load_max_output()

        # self._max_output = v
        # if self.reciprocal_power:
        #     v=100-v
        #
        # self.set_high_power_scale(v)
        # p=self.read_high_power_scale()
        # if p is not None:
        #     self._max_output=p

    def _validate_max_output(self, v):
        return self._validate_number(v)

    def _validate_number(self, v):
        try:
            return float(v)
        except ValueError:
            pass

    def _validate_new(self, new, old, tol=0.001):
        if abs(new - old) > tol:
            return new

    #===============================================================================
    # getters
    #===============================================================================
    def _get_pid_bin(self, temp):
        """
            load pid_bins from file
        """
        p = os.path.join(self.configuration_dir_path, 'pid.csv')
        if not os.path.isfile(p):
            self.warning('No pid.csv file in configuration dir. {}'.format(self.configuration_dir_path))
            return

        lines = parse_file(p, delimiter=',', cast=float)
        for i, li in enumerate(lines):
            if li[0] > temp:
                i = max(0, i - 1)

                return lines[i][1:]
        else:
            t = lines[-1][0]
            self.warning('could not find appropriate bin for in pid file. using pid for {} bin. temp={}'.format(t, temp))
            return lines[-1][1:]

    def _get_autotune_label(self):
        return 'Autotune' if not self.autotuning else 'Stop'

    def _get_heat_algorithm(self):
        return self._heat_algorithm

    def _get_autotune_aggressiveness(self):
        return self._autotune_aggressiveness

    def _get_autotune_setpoint(self):
        return self._autotune_setpoint

    def _get_tru_tune_gain(self):
        return self._tru_tune_gain

    def _get_tru_tune_band(self):
        return self._tru_tune_band

    def _get_enable_tru_tune(self):
        return self._enable_tru_tune

    def _get_output_scale_high(self):
        return self._output_scale_high

    def _get_output_scale_low(self):
        return self._output_scale_low

    def _get_input_scale_high(self):
        return self._input_scale_high

    def _get_input_scale_low(self):
        return self._input_scale_low

    def _get_calibration_offset(self):
        return self._calibration_offset

    def _get_D(self):
        return self._D_

    def _get_I(self):
        return self._I_

    def _get_Pc(self):
        return self._Pc_

    def _get_Ph(self):
        return self._Ph_

    def _get_dead_band(self):
        return self._dead_band

    def _get_control_mode(self):
        return self._control_mode

    def _get_open_loop_setpoint(self):
        return self._olsetpoint

    def _get_closed_loop_setpoint(self):
        return self._clsetpoint

    def _get_thermocouple1_type(self):
        try:
            return tc_map[str(self._thermocouple1_type)]
        except KeyError:
            pass

    def _get_sensor1_type(self):
        try:
            return sensor_map[str(self._sensor1_type)]
        except KeyError:
            pass

    def _get_max_output(self):
        return self._max_output

    #===============================================================================
    # handlers
    #===============================================================================
    def _autotune_fired(self):
        if self.autotuning:
            self.stop_autotune()
        else:
            self.start_autotune()
        self.autotuning = not self.autotuning

    def _configure_fired(self):
        self.edit_traits(view='autotune_configure_view')

    def _refresh_fired(self):
        self.initialization_hook()

    def graph_builder(self, g, **kw):
        g.new_plot(padding_left=40,
                   padding_right=5,
                   zoom=True,
                   pan=True,
                   **kw)
        g.new_plot(padding_left=40,
                   padding_right=5,
                   zoom=True,
                   pan=True,
                   **kw)

        g.new_series()
        g.new_series(plotid=1)

        g.set_y_title('Temp (C)')
        g.set_y_title('Heat Power (%)', plotid=1)

    def get_control_group(self):
        closed_grp = VGroup(
            HGroup(Item('use_pid_bin', label='Set PID',
                        tooltip='Set PID parameters based on setpoint'),
                   Item('use_calibrated_temperature',
                        label='Use Calibration'),
                   Item('coeff_string',show_label=False, enabled_when='use_calibrated_temperature')),
            Item('closed_loop_setpoint',
                 style='custom',
                 label='setpoint',
                 editor=RangeEditor(mode='slider',
                                    format='%0.2f',
                                    low_name='setpointmin', high_name='setpointmax')),
            visible_when='control_mode=="closed"')

        open_grp = VGroup(Item('open_loop_setpoint',
                               label='setpoint',
                               editor=RangeEditor(mode='slider',
                                                  low_name='olsmin', high_name='olsmax'),
                               visible_when='control_mode=="open"'))

        tune_grp=HGroup(Item('enable_tru_tune'),
                        Item('tru_tune_gain', label='Gain', tooltip='1:Most overshot, 6:Least overshoot'))
        cg = VGroup(HGroup(
            Item('control_mode', editor=EnumEditor(values=['closed', 'open'])),
                           Item('max_output', label='Max Output %', format_str='%0.1f'),
                           icon_button_editor('advanced_values_button','cog')),
                    tune_grp,
                    closed_grp, open_grp)
        return cg

    def _advanced_values_button_fired(self):
        self.edit_traits(view='configure_view')

    def get_configure_group(self):
        """
        """

        output_grp = VGroup(Item('output_scale_low', format_str='%0.3f',
                                 label='Scale Low'),
                            Item('output_scale_high', format_str='%0.3f',
                                 label='Scale High'),
                            label='Output',
                            show_border=True)

        autotune_grp = HGroup(Item('autotune', show_label=False, editor=ButtonEditor(label_value='autotune_label')),
                              Item('configure', show_label=False, enabled_when='not autotuning'),
                              label='Autotune',
                              show_border=True)

        input_grp = Group(VGroup(Item('sensor1_type',
                                      # editor=EnumEditor(values=sensor_map),
                                      show_label=False),
                                 Item('thermocouple1_type',
                                      # editor=EnumEditor(values=tc_map),
                                      show_label=False,
                                      visible_when='_sensor1_type==95'),
                                 Item('input_scale_low', format_str='%0.3f',
                                      label='Scale Low', visible_when='_sensor1_type in [104,112]'),
                                 Item('input_scale_high', format_str='%0.3f',
                                      label='Scale High', visible_when='_sensor1_type in [104,112]')),
                          label='Input',
                          show_border=True)

        pid_grp = VGroup(HGroup(Item('Ph', format_str='%0.3f'),
                                Item('Pc', format_str='%0.3f')),
                         Item('I', format_str='%0.3f'),
                         Item('D', format_str='%0.3f'),
                         show_border=True,
                         label='PID')
        return Group(
            HGroup(spring, Item('refresh', show_label=False)),
            autotune_grp,
            HGroup(output_grp,
                   input_grp),
            pid_grp)

    def autotune_configure_view(self):
        v = View('autotune_setpoint',
                 Item('autotune_aggressiveness', label='Aggressiveness'),
                 VGroup(
                     'enable_tru_tune',
                     Group(
                         Item('tru_tune_band', label='Band'),
                         Item('tru_tune_gain', label='Gain', tooltip='1:Most overshot, 6:Least overshoot'),
                         enabled_when='enable_tru_tune'),
                     show_border=True,
                     label='TRU-TUNE+'
                 ),
                 title='Autotune Configuration',
                 kind='livemodal')
        return v

    def control_view(self):
        return View(self.get_control_group())

    def configure_view(self):
        return View(self.get_configure_group())


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('watlowezzone')
    w = WatlowEZZone(name='temperature_controller',
                     configuration_dir_name='diode')
    w.bootstrap()
    w.configure_traits(view='configure_view')
#============================== EOF ==========================
#        #read pid parameters
#        ph = self.read_heat_proportional_band()
#        if ph is not None:
#            self._Ph_ = ph
#
#        pc = self.read_cool_proportional_band()
#        if pc is not None:
#            self._Pc_ = pc
#
#        i = self.read_time_integral()
#        if i is not None:
#            self._I_ = i
#
#        d = self.read_time_derivative()
#        if d is not None:
#            self._D_ = d

# read autotune parameters
#        asp = self.read_autotune_setpoint()
#        if asp is not None:
#            self._autotune_setpoint = asp
#        ttb = self.read_tru_tune_band()
#        if ttb is not None:
#            self._tru_tune_band = ttb
#
#        ttg = self.read_tru_tune_gain()
#        if ttg is not None:
#            self._tru_tune_gain = str(ttg)

#        osl = self.read_output_scale_low()
#        if osl is not None:
#            self._output_scale_low = osl
#
#        osh = self.read_output_scale_low()
#        if osh is not None:
#            self._output_scale_high = osh
