# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import CInt, Str, Bool, Dict, Float, HasTraits, Any
from traitsui.api import View, Item, EnumEditor, RangeEditor
# from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.hardware.core.data_helper import make_bitarray

# ============= standard library imports ========================
# ============= local library imports  ==========================
SPEED_MODES = {'1x':'11', '2x':'10', '4x':'01', '8x':'00'}
from pychron.hardware.kerr.kerr_motor import KerrMotor
'''
    status byte
    0 1 2 3 4 5 6 7
  1 0 0 0 0 0 0 0 1

 18 0 0 0 1 0 0 1 0

 0= moving
 1= comm err
 2= amp enable output signal is HIGH
 3= power sense input signal is HIGH
 4= at speed
 5= vel prof mode
 6= trap prof mode
 7= home in progress

'''

class DiscretePosition(HasTraits):
    position = Float
    value = Float

class KerrStepMotor(KerrMotor):
#    min = CInt
#    max = CInt

    run_current = CInt
    hold_current = CInt
    speed_mode = Str('1x')
    disable_estop = Bool
    disable_limits = Bool
    motor_off = Bool

    discrete_position = Any
    discrete_positions = Dict
    home_offset = Float(0)
    def load_additional_args(self, config):
        super(KerrStepMotor, self).load_additional_args(config)
        for section, option in [('Parameters', 'run_current'),
                                ('Parameters', 'hold_current'),
                                ]:
            self.set_attribute(config, option, section, option, optional=False, cast='int')

        self.set_attribute(config, 'speed_mode', 'Parameters', 'speed_mode', optional=False)
        self.set_attribute(config, 'disable_estop', 'Parameters', 'disable_estop', optional=False, cast='boolean')
        self.set_attribute(config, 'disable_limits', 'Parameters', 'disable_limits', optional=False, cast='boolean')
        self.set_attribute(config, 'motor_off', 'Parameters', 'motor_off', optional=False, cast='boolean')
        # load discrete positions
        section = 'Discrete Positions'
        if config.has_section(section):
            off = self.config_get(config, section, 'offset', cast='int', default=0)
#            self.set_attribute(config, 'home_offset', section, 'offset', cast='int')
            for i, option in enumerate(config.options(section)):
                if option == 'offset':
                    continue

                value = config.get(section, option)
                option = option.replace('_', ' ').capitalize()
                if ',' in value:
                    pos, v = value.split(',')
                else:
                    pos, v = value, 0

                pos = int(pos)
                dp = DiscretePosition(name=option, position=pos + off, value=float(v))
#                dp = DiscretePosition(name=option, position=pos, value=float(v))
#                self.discrete_positions[str(value + off)] = '{:02n}:{}'.format(i + 1, option)
                self.discrete_positions[dp] = '{:02n}:{}'.format(i + 1, option)

    def _get_io_bits(self):
        return ['0',  # bit 4
                '1',
                '1',
                '1',
                '0']  # bit 0

    def _build_io(self):
        cmd = '18'
        iobits = self._get_io_bits()
        v = '000' + ''.join(iobits)
        v = '{:02X}'.format(int(v, 2))
        return cmd + v

    def _discrete_position_changed(self):
        if self.discrete_position:
            dp = self.discrete_position
            self.data_position = float(dp.position)

    def get_discrete_value(self, name=None):
        v = None
        if name is None:
            if self.discrete_position:
                name = self.discrete_position.name

        dp = self.get_discrete_position(name)
        if dp is not None:
            v = dp.value

        return v

    def _convert_value(self, value):
        if value is not None:
            try:
                value = int(value)
            except (TypeError, ValueError):
                if isinstance(value, (list, tuple)):
                    value = ' '.join(value)
                value = value.replace('_', ' ')
                dp = self.get_discrete_position(value)
                if dp:
                    value = int(dp.position)
                print 'disc ', value
            return value

    def get_discrete_position(self, name):

#        for di in self.discrete_positions:
#            print di.name.lower(), name.lower(),di.name.lower()== name.lower
        if name is not None:
            return next((di for di in self.discrete_positions if di.name.lower() == name.lower()), None)

    def _initialize_(self, *args, **kw):
        addr = self.address
        commands = [
                    (addr, '1706', 100, 'stop motor, turn off amp'),
                    (addr, self._build_parameters(), 100, 'set parameters'),
                    (addr, self._build_io(), 100, 'set io'),
                    (addr, '1701', 100, 'turn on amp'),
                    ]
        self._initialize_motor(commands, *args, **kw)


    def _assemble_options_byte(self):
        ob = []
        sbit = SPEED_MODES[self.speed_mode]
        ob.append(sbit)  # 1,2
        ob.append('1' if self.disable_limits else '0')
        ob.append('1' if self.disable_estop else '0')
        ob.append('1' if self.motor_off else '0')
        ob.append('000')
        ob.reverse()

        return ''.join(ob)


    def _build_parameters(self):

        cmd = '56'
        obbyte = self._assemble_options_byte()
#        print obbyte
        op = (int(obbyte, 2), 2)  # '00001011'
        mps = (1, 2)
        rcl = (self.run_current, 2)
        hcl = (self.hold_current, 2)
        tl = (0, 2)
#        print self.run_current,self.hold_current
#        hexfmt = lambda a: '{{:0{}x}}'.format(a[1]).format(a[0])

#        args=self._make_hexstr([op, mps, rcl, hcl, tl])
#        bs = [cmd ] + map(hexfmt, )

#        return cmd+''.join(args)
#        return ''.join(bs)
        return cmd + self._build_hexstr(op, mps, rcl, hcl, tl)

    def _home_motor(self, *args, **kw):
        '''
        '''
        progress = self.progress
        if progress is not None:
            progress = kw['progress']
            progress.increase_max()
            progress.change_message('Homing {}'.format(self.name))

        addr = self.address

        home_control_byte = self._load_home_control_byte()
        home_cmd = '19{:02x}'.format(home_control_byte)

#        cmd = '94'
#        control = 'F6' #'11110110'

        cmd = '34'
        control = '{:02x}'.format(int('10010110', 2))

        v = '{:02x}'.format(int(self.home_velocity))
        a = '{:02x}'.format(int(self.home_acceleration))

#        print control, v,a
#        v = self._float_to_hexstr(self.home_velocity)
#        a = self._float_to_hexstr(self.home_acceleration)
        move_cmd = ''.join((cmd, control, v, a))

        cmds = [  # (addr,home_cmd,10,'=======Set Homing===='),
                (addr, home_cmd, 100, 'Set homing options'),
                (addr, move_cmd, 100, 'Send to Home')]
        self._execute_hex_commands(cmds)


        '''
            this is a hack. Because the home move is in velocity profile mode we cannot use the 0bit of the status byte to
            determine when the move is complete (0bit indicates when motor has reached requested velocity).

            instead we will poll the motor position until n successive positions are equal ie at a limt
        '''

        self.block(4, progress=progress)

        # we are homed and should reset position

        cmds = [(addr, '00', 100, 'reset position')]

        self._execute_hex_commands(cmds)
#
    def _set_motor_position_(self, pos, hysteresis=0, velocity=None, reverse=False):
        '''
        '''
        hpos = self._calculate_hysteresis_position(pos, hysteresis)
        self._motor_position = hpos
        self._desired_position = pos
        #============pos is in mm===========
        addr = self.address
        cmd = '74'
        control = self._load_trajectory_controlbyte(reverse=reverse)
        position = self._float_to_hexstr(hpos)
        if velocity is None:
            velocity = self.velocity
        v = '{:02x}'.format(int(velocity))
        a = '{:02x}'.format(int(self.acceleration))
#        print self.velocity, self.acceleration
        cmd = ''.join((cmd, control, position, v, a))
        cmd = (addr, cmd, 100, 'setting motor steps {}'.format(hpos))
        self._execute_hex_command(cmd)

    def _load_trajectory_controlbyte(self, reverse=False):
        '''
           control byte
                7 6 5 4 3 2 1 0
            97- 1 0 0 1 0 1 1 1

            0=load pos
            1=load vel
            2=load acce
            3=load initial timer count
            4=reverse direction 0=forward
            5=not used
            6=not used
            7=start motion now

        '''
        cb = '10000111'
        if reverse:
            cb = cb[:4] + '1' + cb[-3:]

        return '{:02x}'.format(int(cb, 2))

#    def _get_velocity(self):
#        speed = self._velocity #in um/sec
#        res = 0.5
#        steprate = speed / res
#        result = round(steprate / 25)
#        result = min(max(1, result), 250)
#        print 'calcualtes velocity', result
#        return result




    def _moving(self, verbose=True):
        status_byte = self.read_defined_status(verbose=verbose)

        if status_byte == 'simulation':
            status_byte = 'DFDF'

        status_register = map(int, make_bitarray(int(status_byte[:2], 16)))
        return status_register[7]

    def control_view(self):
        v = View(
#                 Group(
                     Item('discrete_position', show_label=False,
                          editor=EnumEditor(name='discrete_positions'),
                          defined_when='discrete_positions'
                          ),
                     Item('data_position', show_label=False,
                             editor=RangeEditor(mode='slider',
                                                low_name='min',
                                                high_name='max')
                             ),
                     Item('update_position', show_label=False,
                         editor=RangeEditor(mode='slider',
                                            low_name='min',
                                            high_name='max', enabled=False),
                         ),
#                       label=self.display_name,
#                       show_border=True
#                       )

                 )
        return v
# ============= EOF =============================================
