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
from traits.api import Property, Str, Float, CInt, Int, Button
from traitsui.api import View, Item, Group, EnumEditor, HGroup, VGroup, spring

#=============standard library imports ========================
#=============local library imports  ==========================
from pychron.hardware.axis import Axis
from pychron.helpers.filetools import parse_file

from pychron.hardware.results_report import ResultsReport
KINDS = ['Undefined',
              'DC servo motor',
              'Step motor',
              'Commutated step motor',
              'Commutated brushless DC servo motor']
UNITS = ['encoder count',
       'motor step',
       'millimeter',
       'micrometer',
       'inches',
       'milli-inches',
       'micro-inches',
       'degree',
       'gradian',
       'radian',
       'milliradian',
       'microradian']
TRAJECTORY_MODES = ['Trapezoidal',
                 'S-curve',
                 'Jog',
                 'Slave desired position',
                 'Slave actual position',
                 'Slave actual velocity'
                 ]
HOME_SEARCH_MODES = ['Find +0 Position Count',
                   'Find Home and Index Signals',
                   'Find Home Signal',
                   'Find Positive Limit Signal',
                   'Find Negative Limit Signal',
                   'Find Positive Limit and Index',
                   'Find Negative Limit and Index Signals']

COMMAND_MAP = dict(kind='QM',
                 units='SN',
                 encoder_resolution='SU',
                 encoder_full_step_resolution='FR',
                 microstep_factor='QS',
                 average_motor_voltage='QV',
                 maximum_motor_current='QI',
                 gear_constant='QG',
                 tachometer_gain='QT',
                 software_negative_limit='SL',
                 software_positive_limit='SR',
                 trajectory_mode='TJ',
                 home_search_mode='OM',
                 maximum_velocity='VU',
                 velocity='VA',
                 jog_high_speed='JH',
                 jog_low_speed='JW',
                 home_search_high_speed='OH',
                 home_search_low_speed='OL',
                 base_velocity='VB',
                 maximum_acceleration_deceleration='AU',
                 acceleration='AC',
                 deceleration='AG',
                 estop_deceleration='AE',
                 jerk_rate='JK',
                 proportional_gain='KP',
                 integral_gain='KI',
                 derivative_gain='KD',
                 velocity_feed_forward_gain='VF',
                 acceleration_feed_forward_gain='AF',
                 integral_saturation_level='KS',
                 maximum_following_error_threshold='FE',
                 position_deadband='DB',
                 update_interval='CL',
                 reduce_motor_torque_time='QR',
                 reduce_motor_torque_percent='QR',
                 slave_axis='SS',
                 master_slave_reduction_ratio='GR',
                 master_slave_jog_velocity_update='SI',
                 master_slave_jog_velocity_scaling_coefficients='SK',
                 backlash_compensation='BA',
                 linear_compensation='CO',
                 amplifier_io_configuration='ZA',
                 feedback_configuration='ZB',
                 estop_configuration='ZE',
                 following_error_configuration='ZF',
                 hardware_limit_configuration='ZH',
                 software_limit_configuration='ZS'
                 )
SIGNS = ['Positive',
       'Negative']
def binstr_int(v):
    '''
    '''
    return int(v, 2)

def int_binstr(n):
    '''
    '''
    #
    bStr = ''
    #
    if n < 0: raise ValueError, "must be a positive integer"
    if n == 0: return '000000000000'

    i = 0
    while i < 12:
        if n > 0:
            bStr = str(n % 2) + bStr
            n = n >> 1
        else:
            bStr = '0' + bStr
        i += 1

    return bStr

# class NewportAxisHandler(Handler):
#    '''
#        G{classtree}
#    '''
#
#    def closed(self, info, is_ok):
#        '''
#        '''
#        object = info.object
#        if is_ok:
#            object.dump()


class NewportAxis(Axis):
    '''
    '''
    loaded = False

    loadposition = Float



    kind = Property(depends_on='_kind')
    _kind = Int

    units = Property(depends_on='_units')
    _units = Int

    encoder_resolution = Float(enter_set=True, auto_set=False)
    encoder_full_step_resolution = Float(enter_set=True, auto_set=False)
    microstep_factor = Float(enter_set=True, auto_set=False)

    average_motor_voltage = Float(enter_set=True, auto_set=False)
    maximum_motor_current = Float(enter_set=True, auto_set=False)
    gear_constant = Float(enter_set=True, auto_set=False)
    tachometer_gain = Float(enter_set=True, auto_set=False)

    software_negative_limt = Float(enter_set=True, auto_set=False)
    software_positive_limit = Float(enter_set=True, auto_set=False)

    trajectory_mode = Property(depends_on='_trajectory_mode')
    _trajectory_mode = Int

    home_search_mode = Property(depends_on='_home_search_mode')
    _home_search_mode = Int

    maximum_velocity = Float(enter_set=True, auto_set=False)
    base_velocity = Float(enter_set=True, auto_set=False)

    jog_high_speed = Float(enter_set=True, auto_set=False)
    jog_low_speed = Float(enter_set=True, auto_set=False)
    home_search_high_speed = Float(enter_set=True, auto_set=False)
    home_search_low_speed = Float(enter_set=True, auto_set=False)

    maximum_acceleration_deceleration = Float(enter_set=True, auto_set=False)

    estop_deceleration = Float(enter_set=True, auto_set=False)
    jerk_rate = Float(enter_set=True, auto_set=False)

    proportional_gain = Float(enter_set=True, auto_set=False)
    integral_gain = Float(enter_set=True, auto_set=False)
    derivative_gain = Float(enter_set=True, auto_set=False)
    integral_saturation_level = Float(enter_set=True, auto_set=False)

    velocity_feed_forward_gain = Float(enter_set=True, auto_set=False)
    acceleration_feed_forward_gain = Float(enter_set=True, auto_set=False)

    maximum_following_error_threshold = Float(enter_set=True, auto_set=False)
    position_deadband = Float(enter_set=True, auto_set=False)

    update_interval = Float(enter_set=True, auto_set=False)

    reduce_motor_torque_time = Float(enter_set=True, auto_set=False)
    reduce_motor_torque_percent = Float(enter_set=True, auto_set=False)

    slave_axis = Int(enter_set=True, auto_set=False)
    master_slave_reduction_ratio = Float(enter_set=True, auto_set=False)
    master_slave_jog_velocity_update = Float(enter_set=True, auto_set=False)
    master_slave_jog_velocity_scaling_coefficients = Str(enter_set=True, auto_set=False)

    backlash_compensation = Float(enter_set=True, auto_set=False)
    linear_compensation = Float(enter_set=True, auto_set=False)

    amplifier_io_configuration = Property(depends_on='_amplifier_io_configuration')
    _amplifier_io_configuration = Int
    feedback_configuration = Property(depends_on='_feedback_configuration')
    _feedback_configuration = Int
    estop_configuration = Property(depends_on='_estop_configuration')
    _estop_configuration = Int
    following_error_configuration = Property(depends_on='_following_error_configuration')
    _following_error_configuration = Int
    hardware_limit_configuration = Property(depends_on='_hardware_limit_configuration')
    _hardware_limit_configuration = Int
    software_limit_configuration = Property(depends_on='_software_limit_configuration')
    _software_limit_configuration = Int


    read_parameters = Button
    configuring = False

    def _validate_velocity(self, v):
        return self._validate_float(v)

    def _set_velocity(self, v):
        self.nominal_velocity = v

        self.trait_set(_velocity=v, trait_change_notify=False)
        if self.loaded:
            com = self.parent._build_command(COMMAND_MAP['velocity'], xx=self.id, nn=v)
            self.parent.tell(com)

    def _validate_acceleration(self, v):
        return self._validate_float(v)

    def _validate_deceleration(self, v):
        return self._validate_float(v)

    def _set_acceleration(self, v):
        self.nominal_acceleration = v
        self.trait_set(_acceleration=v, trait_change_notify=False)
        if self.loaded:
            com = self.parent._build_command(COMMAND_MAP['acceleration'], xx=self.id, nn=v)
            self.parent.tell(com)

    def _set_deceleration(self, v):
        self.nominal_deceleration = v

        self.trait_set(_deceleration=v, trait_change_notify=False)
        if self.loaded:
            com = self.parent._build_command(COMMAND_MAP['deceleration'], xx=self.id, nn=v)
            self.parent.tell(com)

    def upload_parameters_to_device(self):
        '''
        '''
        for key, cmd in COMMAND_MAP.items():
            if cmd == 'QR':
                continue
            value = getattr(self, key)
            if isinstance(value, str):

                name = '{}S'.format(key.upper()) if not key.endswith('s') else key.upper()

                if cmd in ['ZA', 'ZB', 'ZE', 'ZF', 'ZH', 'ZS']:
                    value = '{:X}H'.format(binstr_int(value))
                elif name != 'MASTER_SLAVE_JOG_VELOCITY_SCALING_COEFFICIENTS':
                    value = globals()[name].index(value)
                    if name == 'TRAJECTORY_MODES':
                        value += 1

            cmd = self.parent._build_command(cmd, xx=self.id, nn=value)
            self.parent.tell(cmd)

        value = '{:n},{:n}'.format(
                               self.reduce_motor_torque_time,
                               self.reduce_motor_torque_percent
                               )
        cmd = self.parent._build_command('QR', xx=self.id, nn=value)
        self.parent.tell(cmd)

    def load(self, path):
        '''
  
        '''
        self.loaded = False


        for key, value in self._get_parameters(path):
            if ',' not in value:
                if key[0] == '_':
                    value = int(value, 16)
                    if key == '_trajectory_mode':
                        value -= 1
                elif key in ['slave_axis', 'sign']:
                    value = int(value)
                else:
                    value = float(value)
            setattr(self, key, value)

        self.nominal_velocity = self.velocity
        self.nominal_acceleration = self.acceleration
        self.nominal_deceleration = self.deceleration
        self.loaded = True

    def load_parameters_from_file(self, path):
        '''

        '''
        self.loaded = False
        # self.kind='Commutated step motor'
        parameters = parse_file(path)
#        with open(path, 'r') as f:
#            parameters = []
#            for line in f:
#                parameters.append(line.strip())

        self._kind = int(parameters[0][-1:])  # QM
        self._unit = int(parameters[1][-1:])  # SN

        self.encoder_resolution = float(parameters[2][3:])  # SU
        self.encoder_full_step_resolution = float(parameters[3][3:])  # FR
        self.microstep_factor = float(parameters[4][3:])  # QS

        self.average_motor_voltage = float(parameters[5][3:])  # QV
        self.maximum_motor_current = float(parameters[6][3:])  # QI
        self.gear_constant = float(parameters[7][3:])  # QG
        self.tachometer_gain = float(parameters[8][3:])  # QT

        self.software_negative_limit = float(parameters[9][3:])  # SL
        self.software_positive_limit = float(parameters[10][3:])  # SR

        self._trajectory_mode = int(parameters[11][-1:]) - 1  # TJ
        self._home_search_mode = int(parameters[12][-1:])  # OM

        self.maximum_velocity = float(parameters[13][3:])  # VU
        self.velocity = float(parameters[14][3:])  # VA
        self.jog_high_speed = float(parameters[15][3:])  # JH
        self.jog_low_speed = float(parameters[16][3:])  # JW

        self.home_search_high_speed = float(parameters[17][3:])  # OH
        self.home_search_low_speed = float(parameters[18][3:])  # OL
        self.base_velocity = float(parameters[19][3:])  # VB

        self.maximum_acceleration_deceleration = float(parameters[20][3:])  # AU
        self.acceleration = float(parameters[21][3:])  # AC
        self.deceleration = float(parameters[22][3:])  # AG
        self.estop_deceleration = float(parameters[23][3:])  # AE

        self.jerk_rate = float(parameters[24][3:])  # JK

        self.proportional_gain = float(parameters[25][3:])  # KP
        self.integral_gain = float(parameters[26][3:])  # KI
        self.derivative_gain = float(parameters[27][3:])  # KD

        self.velocity_feed_forward_gain = float(parameters[28][3:])  # VF
        self.acceleration_feed_forward_gain = float(parameters[29][3:])  # AF

        self.integral_saturation_level = float(parameters[30][3:])  # KS

        self.maximum_following_error_threshold = float(parameters[31][3:])  # FE
        self.position_deadband = float(parameters[32][3:])  # DB

        self.update_interval = float(parameters[33][3:])  # CL

        a, b = parameters[34][3:].split(',')
        self.reduce_motor_torque_time = float(a)  # QR
        self.reduce_motor_torque_percent = float(b)  # QR

        self.slave_axis = int(parameters[35][3:])  # SS
        self.master_slave_reduction_ratio = float(parameters[36][3:])  # GR
        self.master_slave_jog_velocity_update = float(parameters[37][3:])  # SI
        self.master_slave_jog_velocity_scaling_coefficients = parameters[38][3:]  # SK

        self.backlash_compensation = float(parameters[39][3:])  # BA
        self.linear_compensation = float(parameters[40][3:])  # CO

        self._amplifier_io_configuration = int(parameters[41][3:-1], 16)  # ZA
        self._feedback_configuration = int(parameters[42][3:-1], 16)  # ZB
        self._estop_configuration = int(parameters[43][3:-1], 16)  # ZE
        self._following_error_configuration = int(parameters[44][3:-1], 16)  # ZF
        self._hardware_limit_configuration = int(parameters[45][3:-1], 16)  # ZH
        self._software_limit_configuration = int(parameters[46][3:-1], 16)  # ZS

        self.loaded = True
    def _get_kind(self):
        '''
        '''
        return KINDS[self._kind]

    def _set_kind(self, v):
        '''

        '''
        self._kind = KINDS.index(v)

    def _get_units(self):
        '''
        '''
        return UNITS[self._units]

    def _set_units(self, v):
        '''

        '''
        self._units = UNITS.index(v)

    def _get_trajectory_mode(self):
        '''
        '''
        return TRAJECTORY_MODES[self._trajectory_mode]

    def _set_trajectory_mode(self, v):
        '''

        '''
        self._trajectory_mode = TRAJECTORY_MODES.index(v)

    def _get_home_search_mode(self):
        '''
        '''
        return HOME_SEARCH_MODES[self._home_search_mode]

    def _set_home_search_mode(self, v):
        '''

        '''
        self._home_search_mode = HOME_SEARCH_MODES.index(v)

    def _validate_configuration(self, name, value):
        '''

        '''
        if len(value) == 12:
            return value
        else:
            return int_binstr(getattr(self, '_%s' % name))

    def _get_amplifier_io_configuration(self):
        '''
        '''
        return int_binstr(self._amplifier_io_configuration)

    def _set_amplifier_io_configuration(self, v):
        '''

        '''
        self._amplifier_io_configuration = binstr_int(v)

    def _validate_amplifier_io_configuration(self, v):
        '''

        '''
        return self._validate_configuration('amplifier_io_configuration', v)

    def _get_feedback_configuration(self):
        '''
        '''
        return int_binstr(self._feedback_configuration)

    def _set_feedback_configuration(self, v):
        '''

        '''
        self._feedback_configuration = binstr_int(v)

    def _validate_feedback_configuration(self, v):
        '''

        '''
        return self._validate_configuration('feedback_configuration', v)

    def _get_estop_configuration(self):
        '''
        '''
        return int_binstr(self._estop_configuration)

    def _set_estop_configuration(self, v):
        '''

        '''
        self._estop_configuration = binstr_int(v)

    def _validate_estop_configuration(self, v):
        '''

        '''
        return self._validate_configuration('estop_configuration', v)

    def _get_following_error_configuration(self):
        '''
        '''
        return int_binstr(self._following_error_configuration)

    def _set_following_error_configuration(self, v):
        '''

        '''
        self._following_error_configuration = binstr_int(v)

    def _validate_following_error_configuration(self, v):
        '''

        '''
        return self._validate_configuration('following_error_configuration', v)

    def _get_hardware_limit_configuration(self):
        '''
        '''
        return int_binstr(self._hardware_limit_configuration)

    def _set_hardware_limit_configuration(self, v):
        '''

        '''
        self._hardware_limit_configuration = binstr_int(v)

    def _validate_hardware_limit_configuration(self, v):
        '''

        '''
        return self._validate_configuration('hardware_limit_configuration', v)

    def _get_software_limit_configuration(self):
        '''
        '''
        return int_binstr(self._software_limit_configuration)

    def _set_software_limit_configuration(self, v):
        '''

        '''
        self._software_limit_configuration = binstr_int(v)

    def _validate_software_limit_configuration(self, v):
        '''

        '''
        return self._validate_configuration('software_limit_configuration', v)

    def _read_parameters_fired(self):
#        results = []
        results = ResultsReport(axis=self)
        for name, c in COMMAND_MAP.iteritems():
            cmd = self.parent._build_query(c, xx=self.id)
            result = self.parent.ask(cmd)
            results.add(name, c, result)
#            results.append((name, c, cmd, result))
#        return results
        results.edit_traits()

    def _anytrait_changed(self, name, old, new):
#        '''
#
#        '''
        if self.loaded and self.configuring:
            try:
                attr = COMMAND_MAP[name]
                if 'configuration' in name:
                    new = '{:X}H'.format(new)
                elif name == 'trajectory_mode':
                    new += 1

                cmd = self.parent._build_command(attr, xx=self.id, nn=new)
                self.parent.tell(cmd)

            except KeyError, e:
                pass



#            print name
#        print 'ca', name, old, new
#        print name
#        if self.loaded and name not in ['selected', 'text', 'position', 'sign',
#
#                                        '_velocity', 'velocity',
#                                        'load_button'
#                                        ]:
#            if 'configuration' in name:
#                new = '{}H'.fomrat(hex(new)[2:])
#
#            if name[0] == '_':
#                name = name[1:]
#                if name == 'trajectory_mode':
#                    new += 1
#            try:
#                com = self.parent._build_command(COMMAND_MAP[name], xx = self.id, nn = new)
#                self.parent.tell(com)
#            except KeyError, e:
#                print self, e

    def save(self):

        self.info('saving parameters to {}'.format(self.config_path))
        cp = self.get_configuration()

        # ensure 0 is not saved causing the axis to not move
        cp.set('General', 'velocity', max(0.1, self.velocity))
        cp.set('General', 'acceleration', max(0.1, self.acceleration))
        cp.set('General', 'deceleration', max(0.1, self.deceleration))
        for sect in cp.sections():
            for attr in cp.options(sect):
                val = getattr(self, attr)
                if attr == '_trajectory_mode':
                    val += 1

                if attr in ['_amplifier_io_configuration',
                            '_feedback_configuration',
                            '_estop_configuration',
                            '_following_error_configuration',
                            '_hardware_limit_configuration',
                            '_software_limit_configuration',
                            ]:
                    val = '{:X}'.format(val)

                cp.set(sect, attr, val)
#            for items in cp.items(sect):
#                print sect, items, hasattr(self, items[0])
#                cp.set(sect, key, getattr(self, key))

        with open(self.config_path, 'w') as f:
            cp.write(f)

    def full_view(self):
        '''
        '''


        encoder_group = Group(Item('encoder_resolution'),
                            Item('encoder_full_step_resolution'),
                            Item('microstep_factor'),
                            label='Encoder'
                            )
        general_group = Group(Item('name', style='readonly'),
                            Item('id', style='readonly'),
                            Item('kind', editor=EnumEditor(values=KINDS)),
                            Item('units', editor=EnumEditor(values=UNITS)),
                            Item('sign', editor=EnumEditor(values=SIGNS)),
                            Item('trajectory_mode', editor=EnumEditor(values=TRAJECTORY_MODES)),
                            encoder_group,
                            label='General')
        motor_group = Group(Item('average_motor_voltage'),
                          Item('maximum_motor_current'),
                          Item('gear_constant'),
                          Item('tachometer_gain'),
                          label='Motor')


        home_group = Group(Item('home_search_mode', editor=EnumEditor(values=HOME_SEARCH_MODES)),
                         Item('home_search_low_speed'),
                         Item('home_search_high_speed'),
                         label='Home',
                         )


        pid_group = Group(Item('proportional_gain'),
                        Item('integral_gain'),
                        Item('derivative_gain'),
                        Item('integral_saturation_level'),
                        Item('update_interval'),
                        label='PID')

        feed_forward_group = Group(Item('velocity_feed_forward_gain'),
                                 Item('acceleration_feed_forward_gain'),
                                 label='Feed-Forward'
                                 )
        loop_group = Group(pid_group, feed_forward_group,
                         label='Loop')
        limit_group = Group(Item('software_negative_limit'),
                          Item('software_positive_limit'),
                          label='Limits')

        motion_group = Group(Item('maximum_velocity'),
                           Item('velocity'),
                           Item('base_velocity'),
                           Item('maximum_acceleration_deceleration'),
                           Item('acceleration'),
                           Item('deceleration'),
                           Item('estop_deceleration'),
                           Item('jerk_rate'),

                           Group('jog_high_speed',
                                 'jog_low_speed',
                                 label='Jog'),
                           limit_group,
                           label='Motion'
                           )
        misc_group = Group(Item('maximum_following_error_threshold'),
                         Item('position_deadband'),
                         Item('reduce_motor_torque_time'),
                         Item('reduce_motor_torque_percent'),
                         Item('linear_compensation'),
                         Item('backlash_compensation'),
                         label='Misc.')
        master_slave_group = Group(Item('slave_axis'),
                                 Item('master_slave_reduction_ratio'),
                                 Item('master_slave_jog_velocity_update'),
                                 Item('master_slave_jog_velocity_scaling_coefficients'),
                                 label='Master-Slave')
        configuration_group = Group(Item('amplifier_io_configuration'),
                                  Item('feedback_configuration'),
                                  Item('estop_configuration'),
                                  Item('following_error_configuration'),
                                  Item('hardware_limit_configuration'),
                                  Item('software_limit_configuration'),
                                  label='Configuration')
        view = View(
                    VGroup(
                           HGroup(spring, Item('read_parameters', show_label=False)),
                           Group(
                               general_group,
                               motion_group,
                               motor_group,
                               home_group,
                               configuration_group,
                               master_slave_group,
                               loop_group,
                               misc_group,
                               layout='tabbed'
                           )
                          ),
#                  handler = NewportAxisHandler
                  )
        return view
