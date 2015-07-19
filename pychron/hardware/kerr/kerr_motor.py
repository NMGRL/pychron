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

# =============enthought library imports=======================
from traits.api import Float, Property, Bool, Int, CInt, Button
from traitsui.api import View, Item, HGroup, VGroup, EnumEditor, RangeEditor, \
    spring
# from pyface.timer.api import Timer

# =============standard library imports ========================
import struct
import binascii
# =============local library imports  ==========================
from kerr_device import KerrDevice
from pychron.hardware.core.data_helper import make_bitarray
import time
from pychron.globals import globalv
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.hardware.linear_mapper import LinearMapper
from pychron.core.helpers.timer import Timer
from pychron.consumer_mixin import ConsumerMixin
from pychron.core.ui.qt.progress_editor import ProgressEditor
# from pyface.progress_dialog import ProgressDialog

SIGN = ['negative', 'positive']


class KerrMotor(KerrDevice, ConsumerMixin):
    """
        Base class for motors controller by a kerr microcontroller board

    """
    use_initialize = Bool(True)
    use_hysteresis = Bool(False)
    hysteresis_value = Float(0)  # nominal value to for hysteresis

    velocity = Property
    _velocity = Float
    acceleration = Float
    home_delay = Float
    home_velocity = Float
    home_acceleration = Float
    homing_position = Int
    home_at_startup = Bool(True)
    home_position = CInt
    home_limit = CInt

    min = Float(0)
    max = Float(100)
    steps = Int(137500)
    min_steps = Int(0)
    sign = Float

    enabled = Bool(False)
    timer = None

    data_position = Property(depends_on='_data_position')
    _data_position = Float

    update_position = Float
    nominal_position = Float

    progress = None

    _motor_position = CInt
    doing_hysteresis_correction = False
    do_hysteresis = False
    display_name = Property
    display_name_color = 'brown'

    locked = False
    units = 'mm'

    home_button = Button('Home')

    home_status = Int

    def set_value(self, value, block=False):
        if self.data_position != value:
            self.enabled = False
            value = self._convert_value(value)
            self.info('setting data position {}'.format(value))
            self._set_motor(value)
            #            self.data_position = value
            if block:
                self.info('waiting for move to complete')
                self.block()
                self.info('move complete')
            self.enabled = True
        else:
            self.info('not changing pos {}=={}'.format(self.data_position, value))

        return True

    def load_additional_args(self, config):
        """
        """
        args = [
            ('Motion', 'steps', 'int'),
            ('Motion', 'min_steps', 'int'),
            ('Motion', 'sign'),
            ('Motion', 'velocity'),
            ('Motion', 'acceleration'),

            ('Homing', 'home_delay'),
            ('Homing', 'home_velocity'),
            ('Homing', 'home_acceleration'),
            ('Homing', 'home_at_startup', 'boolean'),
            ('Homing', 'home_position'),
            ('Homing', 'home_limit'),

            ('General', 'min'),
            ('General', 'max'),
            ('General', 'nominal_position'),
            ('General', 'units')
        ]
        for args in args:
            if len(args) == 3:
                section, key, cast = args
            else:
                cast = 'float'
                section, key = args

            self.set_attribute(config, key, section, key, cast=cast)

        if config.has_option('Motion', 'hysteresis'):
            '''
                if hysteresis is <0
                correction is done when moving in the negative direction

                if hysteresis is >0
                correction is done when moving in the positive direction
            '''

            self.hysteresis_value = self.config_get(config, 'Motion', 'hysteresis', cast='int')
        # self.use_hysteresis = True
        #         else:
        #             self.use_hysteresis = False

        if config.has_option('General', 'initialize'):
            self.use_initialize = self.config_get(config, 'General', 'initialize', cast='boolean')

        mi = self.min
        ma = self.max

        if self.sign == -1:
            tm = mi
            mi = ma
            ma = tm

        self.linear_mapper = LinearMapper(
            low_data=mi,
            high_data=ma,
            low_step=int(self.min_steps),
            high_step=int(self.steps))

    def initialize(self, *args, **kw):
        """
        """
        try:
            self.progress = kw['progress']
        except KeyError:
            pass

        self._start_initialize(*args, **kw)
        self._initialize(*args, **kw)
        self._finish_initialize()

        if self.nominal_position is not None:
            move_to_nominal = True
            if not globalv.ignore_initialization_questions:
                move_to_nominal = self.confirmation_dialog(
                    'Would you like to set the {} motor to its nominal pos of {}'.format(self.name.upper(),
                                                                                         self.nominal_position))

            if move_to_nominal:
                # move to the home position
                np = self.nominal_position
                self._set_motor(self.nominal_position, main=False)

                timed_out = False
                if self.timer:
                    timeout = 60
                    # timer stops when move has completed
                    timed_out = self.timer.wait_for_completion(timeout=timeout)

                if timed_out:
                    msg = 'move to nominal position {} timed out after {}s'.format(np, timeout)
                    self.warning(msg)
                    self.warning_dialog(msg)
                else:
                    self.info('move to nominal position {} complete'.format(np))

                    #                 self._set_data_position(self.nominal_position)
                    #                 self.block(5, progress=self.progress)

        # remove reference to progress
        self.progress = None
        self.enabled = True

        self.setup_consumer(buftime=500)

        return True

    def reset_position(self, motor_off=True, position=None):
        """
            1707 amp on
            1706 amp off
        """
        addr = self.address
        # b = '6' if motor_off else '7'

        cmds = []
        if motor_off:
            cmd, msg = '1706'
            cmds.append((addr, '1706', 100, 'Motor OFF'))

        if position is not None:
            cmd, msg = '50{:04X}'.format(position), 'Setting home position as {}'.format(position)
        else:
            cmd, msg = '00', 'Reset Position'

        cmds.append((addr, cmd, 100, msg))
        if motor_off:
            cmds.append((addr, '1707', 100, 'Moto ON'))

            # if motor_off:
            # cmds = [(addr, '', 100, )]

        # cmds = [(addr, '170{}'.format(b), 100, 'Stop motor'),
        #         (addr, cmd, 100, msg),
        #         ()]
        self._execute_hex_commands(cmds)
        self._motor_position = 0

    # PIC Commands
    def read_status(self, cb, verbose=True):
        if isinstance(cb, str):
            cb = '{:02x}'.format(int(cb, 2))

        addr = self.address
        cb = '13{}'.format(cb)
        cmd = self._build_command(addr, cb)
        status_byte = self.ask(cmd, is_hex=True,
                               delay=100,
                               nbytes=3,
                               verbose=verbose,
                               info='get status byte')
        return status_byte

    def read_defined_status(self, verbose=True):

        addr = self.address
        cmd = '0E'
        cmd = self._build_command(addr, cmd)
        status_byte = self.ask(cmd, is_hex=True,
                               delay=100,
                               nbytes=2,
                               info='get defined status',
                               verbose=verbose)
        return status_byte

    def read_home_position(self):
        addr = self.address

        cb = int('00010000', 2)
        cmd = '13{:02X}'.format(cb)
        cmd = self._build_command(addr, cmd)
        position_byte = self.ask(cmd, is_hex=True,
                                 delay=100,
                                 nbytes=6,
                                 info='get home position',
                                 verbose=True)
        return self._parse_position(position_byte)

    def is_moving(self):
        return not self.enabled

    def progress_update(self, progress, signal):
        while not signal.is_set():
            pos = self._read_motor_position(verbose=False)
            if progress is not None:
                progress.change_message('{} position= {}'.format(self.name, pos),
                                        auto_increment=False)
                #                 do_after(25, progress.change_message, '{} position = {}'.format(self.name, pos))
            time.sleep(0.5)

    def block(self, n=3, tolerance=1, progress=None, homing=False):
        """
        """
        fail_cnt = 0
        pos_buffer = []

        while not self.parent.simulation:

            steps = self.load_data_position(set_pos=False)
            if homing:
                invoke_in_main_thread(self.trait_set, homing_position=steps)

            if progress is not None:
                progress.change_message('{} position = {}'.format(self.name, steps),
                                        auto_increment=False)

            if steps is None:
                fail_cnt += 1
                if fail_cnt > 5:
                    break
                continue

            pos_buffer.append(steps)
            if len(pos_buffer) == n:
                if abs(float(sum(pos_buffer)) / n - steps) < tolerance:
                    break
                else:
                    pos_buffer.pop(0)

            time.sleep(0.1)

        if fail_cnt > 5:
            self.warning('Problem Communicating')

    def load_data_position(self, set_pos=True):
        """
        """
        steps = self._read_motor_position(verbose=False)
        if steps is not None:
            pos = self.linear_mapper.map_data(steps)
            pos = max(self.min, min(self.max, pos))
            self.update_position = pos
            if set_pos:
                self._data_position = pos

            self.debug('Load data position {} {} steps= {}'.format(
                pos, self.units,
                steps))
            return steps

    def timer_factory(self):
        """
            reuse timer if possible
        """
        timer = self.timer

        func = self._update_position
        if timer is None:
            self._not_moving_count = 0
            timer = Timer(250, func)
        else:
            if timer.isActive():
                self.debug('reusing old timer')
            else:
                self._not_moving_count = 0
                timer = Timer(250, func)

        return timer

    # private
    def _initialize(self, *args, **kw):
        addr = self.address
        commands = [(addr, '1706', 100, 'stop motor, turn off amp'),
                    (addr, self._build_io(), 100, 'configure io pins'),
                    (addr, self._build_gains(), 100, 'set gains'),
                    (addr, '1701', 100, 'turn on amp')]
        # (addr, '00', 100, 'reset position'),
        # (addr, '1201', 100, 'set status')
        # (addr, '0b', 100, 'clear bits')]
        self._initialize_motor(commands, *args, **kw)

    def _initialize_motor(self, commands, *args, **kw):
        self.load_data_position()

        self._execute_hex_commands(commands)
        if self.home_at_startup:
            self.info('============ HOME AT STARTUP =============')
            self._execute_hex_commands([(self.address, '00', 100, 'reset position')])
            self._home_motor(*args, **kw)
        elif self.homing_position:
            self.reset_position(position=self.homing_position)

        self.load_data_position()

    def _home_motor(self, progress=None, *args, **kw):

        if progress is not None:
            progress.increase_max()
            progress.change_message('Homing {}'.format(self.name))

        addr = self.address

        cmd = '94'
        control = 'F6'

        v = self._float_to_hexstr(self.home_velocity)
        a = self._float_to_hexstr(self.home_acceleration)
        move_cmd = ''.join((cmd, control, v, a))

        home_control_byte = self._load_home_control_byte()
        home_cmd = '19{:02x}'.format(home_control_byte)
        self._clear_bits()
        cmds = [(addr, home_cmd, 100, '=======Set Homing===='),
                (addr, move_cmd, 100, 'Send to Home')]
        self._execute_hex_commands(cmds)
        # self.block(4, progress=progress, homing=True)
        # wait until homing signal set

        hbit = 5 if self.home_limit == 1 else 6
        while 1:
            steps = self.load_data_position(set_pos=False)
            invoke_in_main_thread(self.trait_set, homing_position=steps)
            status = self.read_defined_status()

            if not self._test_status_byte(status, setbits=[7]):
                break
            if self._test_status_byte(status, setbits=[7,hbit]):
                break
            time.sleep(0.25)

        pos = self.read_home_position()
        cmds = [(addr, '00', 100, 'reset position')]
        self._execute_hex_commands(cmds)
        print 'ppppp', pos
        # self.update_configuration(homing={'home_position': pos})

    def _parse_position(self, pos):
        if pos is not None:
            pos = pos[2:-2]
            return self._hexstr_to_float(pos)

    def _test_status_byte(self, status, setbits):
        b = '{:08b}'.format(int(status[:2], 16))
        print b
        # status_register = map(int, make_bitarray(int(status_byte[:2], 16)))
        return all(bool(int(b[7 - si])) for si in setbits)

    def _home_motor2(self, progress=None, *args, **kw):
        """
        """
        if progress is not None:
            progress.increase_max()
            progress.change_message('Homing {}'.format(self.name))

        addr = self.address

        cmd = '94'
        # control = 'F6'
        control = '8E'

        v = self._float_to_hexstr(self.home_velocity)
        a = self._float_to_hexstr(self.home_acceleration)
        move_cmd = ''.join((cmd, control, v, a, '00'))

        #         home_control_byte = self._load_home_control_byte()
        #         home_cmd = '19{:02x}'.format(home_control_byte)

        cmds = [
            #                 (addr, home_cmd, 100, '=======Set Homing===='),
            (addr, move_cmd, 100, 'Send to Home')]
        self._execute_hex_commands(cmds)

        '''
            this is a hack. Because the home move is in velocity profile mode we cannot use the 0bit of the status byte to
            determine when the move is complete (0bit indicates when motor has reached requested velocity).

            instead we will poll the motor position until n successive positions are equal ie at a limt
        '''

        self.block(4, progress=progress, homing=True)

        # we are homed and should reset position

        cmds = [(addr, '00', 100, 'reset position')]

        self._execute_hex_commands(cmds)

    def _moving(self, verbose=True):
        status_byte = self.read_defined_status(verbose=verbose)

        if status_byte in ('simulation', None):
            status_byte = 'DFDF'
        status_register = map(int, make_bitarray(int(status_byte[:2], 16)))
        return not status_register[7]

    def _clear_bits(self):
        cmd = (self.address, '0b', 100, 'clear bits')
        self._execute_hex_command(cmd)

    def _read_motor_position(self, **kw):
        addr = self.address
        cmd = '13'
        control = '01'

        cmd = ''.join((cmd, control))
        cmd = (addr, cmd, 100, '')

        pos = self._execute_hex_command(cmd, nbytes=6, **kw)

        # trim off status and checksum bits
        if pos is not None:
            pos = pos[2:-2]
            pos = self._hexstr_to_float(pos)
            #            self._motor_position = pos
            return pos

    def _load_home_control_byte(self):
        """
           control byte
                7 6 5 4 3 2 1 0
            97- 1 0 0 1 0 1 1 1
            0=capture home on limit1
            1=capture home on limit2
            2=turn motor off on home
            3=capture home on home
            4=stop abruptly
            5=stop smoothly
            6,7=not used- clear to 0
        """
        if self.home_limit == 1:
            bs = '00010001'
        else:
            bs = '00010010'

        return int(bs, 2)
        # return int('00010011', 2)

    def _load_trajectory_controlbyte(self):
        """
           control byte
                7 6 5 4 3 2 1 0
            97- 1 0 0 1 0 1 1 1

            0=load pos
            1=load vel
            2=load acce
            3=load pwm
            4=enable servo
            5=profile mode 0=trap 1=vel
            6=direction trap mode 0=abs 1=rel vel mode 0=for. 1=back
            7=start motion now

        """

        return '{:02x}'.format(int('10010111', 2))

    def _calculate_hysteresis_position(self, pos, hysteresis):
        hpos = pos + hysteresis
        #         self._hysteresis_correction = 0
        #         if hysteresis:
        hpos = max(self.min_steps, min(self.steps, hpos))
        #             if hpos > self.max:
        #                 self._hysteresis_correction = hpos - self.max
        #                 hpos = self.max
        #             elif hpos < self.min:
        #                 self._hysteresis_correction = hpos - self.min
        #                 hpos = self.min
        #             else:
        #                 self._hysteresis_correction = hysteresis
        return hpos

    def _update_position(self):
        """
        """

        if self._moving(verbose=False):
            self.enabled = False

        # if not self._check_status_byte(0):
        #            self.enabled = False

        else:
            #             if self.use_hysteresis and \
            if self.hysteresis_value and \
                    not self.doing_hysteresis_correction and \
                    self.do_hysteresis:
                # move to original desired position at half velocity
                #                    print 'mp',self._motor_position, self.hysteresis_value
                self._set_motor_position(
                    self._desired_position,
                    velocity=self.velocity / 2
                )
                self.doing_hysteresis_correction = True
            else:
                self.enabled = True
                if self.timer is not None:
                    self.timer.Stop()
                    #                     self.update_position = self._data_position
                    time.sleep(0.25)
                    self.load_data_position(set_pos=False)

        if not self.enabled:
            self.load_data_position(set_pos=False)

    def _set_motor(self, pos, main=True):
        if self._data_position != pos or not self._data_position:
            self.info('setting motor in data space {:0.3f}'.format(float(pos)))

            self._data_position = pos
            lm = self.linear_mapper
            steps = lm.map_steps(pos)

            hv = 0
            hysteresis = self.hysteresis_value
            if hysteresis:
                self.do_hysteresis = False
                if hysteresis < 0:
                    use_hysteresis = self._motor_position > steps
                else:
                    use_hysteresis = self._motor_position < steps

                if use_hysteresis:
                    self.do_hysteresis = True
                    self.doing_hysteresis_correction = False
                    hv = hysteresis

            self._set_motor_position(steps, hv)

            def launch():
                self.timer = self.timer_factory()

            if main:
                invoke_in_main_thread(launch)
            else:
                launch()

                #            if self.parent.simulation:
                #                self.update_position = self._data_position

    def _set_motor_position(self, pos, hysteresis=0, velocity=None):
        """
        """
        hpos = self._calculate_hysteresis_position(pos, hysteresis)
        self._desired_position = pos
        self._motor_position = hpos
        #        self._motor_position =npos= min(self.max, max(self.min, pos + hysteresis))
        # ============pos is in mm===========
        addr = self.address
        cmd = 'D4'
        control = self._load_trajectory_controlbyte()
        position = self._float_to_hexstr(hpos)
        if velocity is None:
            velocity = self.velocity
        v = self._float_to_hexstr(velocity)

        a = self._float_to_hexstr(self.acceleration)
        #        print cmd, control, position, v, a
        cmd = ''.join((cmd, control, position, v, a))
        cmd = (addr, cmd, 100, 'setting motor steps {}'.format(hpos))

        self._execute_hex_command(cmd)

    def _convert_value(self, value):
        return value

    def _float_to_hexstr(self, f, endianness='little'):
        f = max(0, f)
        fmt = '%si' % ('<' if endianness == 'little' else '>')
        return binascii.hexlify(struct.pack(fmt, int(f)))

    def _hexstr_to_float(self, h, endianness='little'):
        # fmt = '%si'.('<' if endianness == 'little' else '>')
        fmt = '<i' if endianness == 'little' else '>i'
        try:
            return struct.unpack(fmt, h.decode('hex'))[0]
        except Exception, e:
            print 'exception', e

    def _build_hexstr(self, *hxlist):
        ss = []
        for args in hxlist:
            if len(args) == 2:
                v, n = args
                flip = False
            else:
                v, n, flip = args

            fmt = '{{:0{}x}}'.format(n)
            s = fmt.format(v)
            if flip:
                s = '{}{}'.format(s[2:], s[:2])

            ss.append(s)

        return ''.join(ss)

        # hexfmt = lambda a: '{{:0{}x}}'.format(a[1]).format(a[0])
        # return ''.join(map(hexfmt, hxlist))

    def _build_io(self):
        return '1800'

    def _build_gains(self):
        """
            F6  B004 2003 F401 E803 FF 00 E803 01 01 01
            cmd p    d    i    il   ol cl el   sr db sm

            B004 2003 F401 B004 FF 00 6400 010101

            0064 03e8 0000 0000 ff 00 0fa0 01 01 01
        """
        flip_nibbles = True

        p = (100, 4, flip_nibbles)
        d = (1000, 4, flip_nibbles)
        i = (0, 4, flip_nibbles)
        il = (0, 4, flip_nibbles)
        ol = (255, 2)
        cl = (0, 2)
        el = (4000, 4, flip_nibbles)
        sr = (1, 2)
        db = (1, 2)
        sm = (1, 2)
        gains = self._build_hexstr(p, d, i, il, ol, cl, el, sr, db, sm)
        return 'F6{}'.format(gains)

    def _start_initialize(self, *args, **kw):
        self.info('init {}'.format(self.name))

    def _finish_initialize(self):
        """
        """

    # handlers
    def _update_position_changed(self):
        # self.debug('*****************************update position {}'.format(self.update_position))
        try:
            self.progress.change_message('{} position = {}'.format(self.name, self.update_position),
                                         auto_increment=False)
        except AttributeError:
            # self.progress is None
            pass

    def _home_button_fired(self):
        self.home_status = 1
        self._home_motor()
        self.load_data_position()
        self.home_status = 2
        self.information_dialog('Homing Complete')
        self.home_status = 0

    # property get set
    def _get_velocity(self):
        return self._velocity

    def _set_velocity(self, v):
        self._velocity = v

    def _get_display_name(self):
        return self.name.capitalize()

    def _get_data_position(self):
        return self._data_position

    def _set_data_position(self, pos):
        self.add_consumable((self._set_motor, pos))

    # view
    def control_view(self):
        return View(
            Item('data_position', show_label=False,
                 editor=RangeEditor(mode='slider',
                                    format='%0.3f',
                                    low_name='min',
                                    high_name='max')),
            Item('update_position', show_label=False,
                 editor=RangeEditor(mode='slider',
                                    format='%0.3f',
                                    low_name='min',
                                    high_name='max', enabled=False)),
            HGroup(
                Item('home_status',
                     show_label=False,
                     editor=ProgressEditor(min=0, max=2)),
                Item('homing_position', style='readonly', width=150,
                     label='Steps'),
                Item('home_button', show_label=False), spring))

    def traits_view(self):
        """
        """
        return View(VGroup(
            HGroup('min', 'max', label='Limits', show_border=True),
            VGroup('velocity', 'acceleration', Item('sign', editor=EnumEditor(values={'negative': -1, 'positive': 1})),
                   label='Move', show_border=True),
            VGroup('home_velocity', 'home_acceleration', 'homing_position', label='Home', show_border=True)))

        # ============= EOF ====================================

# def _check_status_byte(self, check_bit):
#        '''
#        return bool
#        check bit =0 False
#        check bit =1 True
#        '''
#        status_byte = self.read_defined_status()
#
#        if status_byte == 'simulation':
#            status_byte = 'DFDF'
#
#        status_register=map(int,make_bitarray(int(status_byte[:2], 16)))
#        print status_register
#        #2 status bytes were returned ?
#        if len(status_byte) > 4:
#            status_byte = status_byte[-4:-2]
#
#        else:
#            status_byte = status_byte[:2]
#
#        try:
#            status_register = self._check_bits(int(status_byte, 16))
#        except Exception, e:
#            self.warning('kerr_motor:228 {}'.format(str(e)))
#            status_register = []
#            if self.timer is not None:
#                self.timer.Stop()
#        '''
#        if X bits is set to one its index will be in the status register
#        '''
#
#        return check_bit in status_register
#     def _set_data_position2(self, pos):
#         '''
#
#             this is a better solution than al deinos (mass spec) for handling positioning of a
#             linear drive.  Al sets the focused position from 0-100. this means if you change the drive sign
#             (in affect changing the homing position +tive or -tive) you also have to change the focused position
#
#             example
#             drive sign =-1
#             home pos= 99
#
#             drive sign =1
#             home pos = 1
#
#             this seems wrong. the solution that follows sets the focused position in % distance from home
#
#             focus_beam_pos=0.01 #1%
#             dr_sign=1
#
#             #normalize the input value to 1
#             pos=pos/(max-min)
#
#             if dr_sign==-1:
#                 pos=1-pos
#
#             #scale pos to the total number of motor steps ** minus the focused position in motor steps **
#             focus_pos_msteps=motor_steps*focus_pos
#
#             pos_msteps= (motor_steps-focus_pos_msteps) * pos
#
#
#             drive a few steps past desired position then back to desired position
#             this takes out any lash in the gears
#
#         '''
#         self.info('setting motor in data space {:0.3f}'.format(float(pos)))
#         if self._data_position != pos:
#
#             self._data_position = pos
#
#             pos /= float((self.max - self.min))
#             if self.sign == -1.0:
#                 pos = 1 - pos
#
#             steps = int((1 - self.home_position) * self.steps * pos)
#             hysteresis = 0
#             self.do_hysteresis = False
#             if self.hysteresis_value < 0:
#                 use_hysteresis = self._motor_position > steps
#             else:
#                 use_hysteresis = self._motor_position < steps
#
#             if use_hysteresis and self.use_hysteresis:
#                 self.do_hysteresis = True
#                 self.doing_hysteresis_correction = False
#                 hysteresis = self.hysteresis_value
#
#             self._set_motor_position_(steps, hysteresis)
#             if not self.parent.simulation:
#                 #invoke in gui thread because in position update can be triggered from a RemoteHardware thread
#                 def launch_timer():
#                     self.timer = Timer(400, self._update_position)
#                 invoke_in_main_thread(launch_timer)
#
#             else:
#                 self.update_position = self._data_position
