# ===============================================================================
# Copyright 2016 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Int, Bool, Float, CInt
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.hardware.base_linear_drive import BaseLinearDrive

ERROR_MAP = {'6': 'An I/O is already set to this type. Applies to non-General Purpose I/O.',
             '8': 'Tried to set an I/O to an incorrect I/O type.',
             '9': 'Tried to write to I/O set as Input or is "TYPED".',
             '10': 'Illegal I/O number.',
             '11': 'Incorrect CLOCK type.',
             '12': 'Illegal Trip / Capture',
             '20': 'Tried to set unknown variable or flag. Trying to set an undefined variable of flag. '
                   'Also could be a typo.',
             '21': 'Tried to set an incorrect value. Many variables have a range such as the Run Current (RC) '
                   'which is 1 to 100%. As an example, you cannot set the RC to 110%.',
             '22': 'VI is set greater than or equal to VM. The Initial Velocity is set equal to, or higher than the '
                   'Maximum Velocity. VI must be less than VM.',
             '23': 'VM is set less than or equal to VI. The Maximum Velocity is set equal to, or lower than the '
                   'Initial Velocity. VM must be greater than VI.',
             '24': 'Illegal data entered. Data has been entered that the device does not understand.',
             '25': 'Variable or flag is read only. Read only flags and variables cannot be set.',
             '26': 'Variable or flag is not allowed to be incremented or decremented. IC and DC cannot be used on '
                   'variables or flags such as Baud and Version.',
             '27': 'Trip not defined.Trying to enable a trip that has not yet been defined.',
             '28': 'WARNING! Trying to redefine a program label or variable. This can be caused when you download '
                   'a program over a program already saved. Before downloading a new or edited program, type <FD> '
                   'and press ENTER to return the device to the Factory Defaults. '
                   'You may also type <CP> and press ENTER to Clear the Program.',
             '29': 'Trying to redefine a built in command, variable or flag.',
             '30': 'Unknown label or user variable. Trying to Call or Branch to a Label or '
                   'Variable that has not yet been defined.',
             '31': 'Program label or user variable table is full. '
                   'The table has a maximum capacity of 22 labels and/or user variables.',
             '32': 'Trying to set a label (LB). You cannot name a label and then try to set it to a value. '
                   'Example: Lable P1 (LB P1 ). The P1 cannot be used to set a variable such as P1=1000.',
             '33': 'Trying to SET an Instruction.',
             '34': 'Trying to Execute a Variable or Flag',
             '35': 'Trying to Print Illegal Variable or Flag',
             '36': 'Illegal Motor Count to Encoder Count Ratio',
             '37': 'Command, Variable or Flag Not Available in Drive',
             '38': 'Missing parameter separator',
             '39': 'Trip on Position and Trip on Relative Distance not allowed together',
             '40': 'Program not running. If HOLD (H) is entered in Immediate Mode and a program is not running.',
             '41': 'Stack overflow',
             '42': 'Illegal program address. Tried to Clear, List, Execute, etc. an incorrect Program address.',
             '43': 'Tried to overflow program stack. Calling a Sub-Routine or Trip Routine with no Return.',
             '44': 'Program locked. User Programs can be Locked with the <LK> command. Once Locked, '
                   'the program cannot be listed or edited in any way.',
             '45': 'Trying to Overflow Program Space.',
             '46': 'Not in Program Mode.',
             '47': 'Tried to Write to Illegal Flash Address',
             '48': 'Program Execution stopped by I/O set as Stop.',
             '60': 'Not used',
             '61': 'Trying to set illegal BAUD rate. The only Baud Rates accepted are those listed on the '
                   'Properties Page of IMS Terminal. (4,800, 9,600, 19,200, 38,400, 115,200)',
             '62': 'IV already pending or IF Flag already TRUE.',
             '63': 'Character over-run. Character was received. Processor did not have time to process it and it'
                   ' was over-written by the next character.',
             '64': 'Startup Calibration failed (Hybrid only)',
             '70': 'FLASH Check Sum Fault',
             '71': 'Internal Temperature Warning, 10C to Shutdown',
             '72': 'Internal Over TEMP Fault, Disabling Drive',
             '73': 'Tried to SAVE while moving',
             '74': 'Tried to Initialize Parameters (IP) or Clear Program (CP) while Moving',
             '75': 'Linear Overtemperature Error (For units without Internal Over Temp)',
             '80': 'HOME switch not defined. Attempting to do a HOME (H) sequence but '
                   'the Home Switch has not yet been defined.',
             '81': 'HOME type not defined. The HOME (HM or HI) Command has been programmed '
                   'but with no type or an illegal type. '
                   '(Types = 1, 2, 3, or 4)',
             '82': 'Went to both LIMITS and did not find home. The motion encroached both limits '
                   'but did not trip the Home switch. Indicates a possible badswitch or a bad circuit.',
             '83': 'Reached plus LIMIT switch. The LIMIT switch in the plus directionwas tripped.',
             '84': 'Reached minus LIMIT switch. The LIMIT switch in the minus directionwas tripped.',
             '85': 'MA or MR is not allowed during a HOME and a HOME is not allowed while the device is in motion.',
             '86': 'Stall detected. The Stall Flag (ST) has been set to 1.',
             '87': 'MDrive In Clock Mode, JOG not allowed',
             '88': 'MDrive Following error',
             '89': 'MDrive Reserved',
             '90': 'Motion Variables are too low switching to EE=1',
             '91': 'Motion stopped by I/O set as Stop.',
             '92': 'Position Error in Closed loop. motor will attempt tp position the shaft within the deadband, '
                   'After failing 3 attempts Error 92 will be generated.Axis will continue to function normally.',
             '93': 'MR or MA not allowed while correcting position at end of previous MR or MA.',
             '94': 'Clear Locked Rotor Fault not allowed while in Motion. MDrive Hybrid products(MAI) only.'}


class BaseMDrive(BaseLinearDrive):
    initial_velocity = CInt
    acceleration = CInt
    deceleration = CInt
    _velocity = Int

    run_current = CInt
    use_encoder = Bool
    steps_per_turn = CInt
    turns_per_mm = Float
    slew_velocity = CInt

    _slewing = False

    def load_additional_args(self, config):
        args = [
            ('Motion', 'steps', 'int'),
            ('Motion', 'min_steps', 'int'),
            ('Motion', 'sign'),
            ('Motion', 'velocity', 'int'),
            ('Motion', 'slew_velocity'),
            ('Motion', 'initial_velocity'),
            ('Motion', 'acceleration'),
            ('Motion', 'deceleration'),
            ('Motion', 'run_current'),
            ('Motion', 'use_encoder', 'boolean'),
            ('Motion', 'turns_per_mm'),

            ('Homing', 'home_delay'),
            ('Homing', 'home_velocity'),
            ('Homing', 'home_acceleration'),
            ('Homing', 'home_at_startup', 'boolean'),
            ('Homing', 'home_position'),
            ('Homing', 'home_limit'),

            ('General', 'min'),
            ('General', 'max'),
            ('General', 'nominal_position'),
            ('General', 'units')]
        self._load_config_attributes(config, args)

        self.linear_mapper_factory()
        return True

    def initialize(self, *args, **kw):
        if super(BaseMDrive, self).initialize(*args, **kw):
            self.set_use_encoder(self.use_encoder)
            if self.use_encoder:
                self.steps_per_turn = 2048
            else:
                self.steps_per_turn = 51200

            for attr in ('initial_velocity', 'velocity', 'acceleration', 'deceleration', 'run_current'):
                v = getattr(self, attr)
                if v:
                    func = getattr(self, 'set_{}'.format(attr))
                    func(v)
            return True

    def is_simulation(self):
        return self.simulation

    def move_absolute(self, pos, block=True, units='steps'):
        pos = self._get_steps(pos, units)
        self._move(pos, False, block)

    def move_relative(self, pos, block=True, units='steps'):
        self.debug('move relative pos={}, block={}, units={}'.format(pos, block, units))
        pos = self._get_steps(pos, units)
        self.debug('converted steps={}'.format(pos))
        self._move(pos, True, block)

    def get_position(self, units='steps'):
        steps = self.read_position()
        self.debug('read position steps={}'.format(steps))
        pos = self._convert_steps(steps, units)
        self.debug('converted position= {} ({})'.format(pos, units))
        return pos

    def slew(self, scalar):
        if not self._slewing:
            v = self.slew_velocity * scalar
            self.set_slew(v)
            self._slewing = True

    def stop_drive(self):
        self._slewing = False
        self.set_slew(0)

    def set_initial_velocity(self, v):
        self._set_var('VI', v)

    def set_velocity(self, v):
        self._set_var('VM', v)

    def set_acceleration(self, a):
        self._set_var('A', a)

    def set_slew(self, v):
        self._set_var('SL', v)

    def set_encoder_position(self, v):
        self._set_var('P', v)

    def set_use_encoder(self, b):
        self._set_var('EE', '{:b}'.format(b))

    def set_run_current(self, rc):
        self._set_var('RC', rc)

    def moving(self):
        return self._moving()

    def block(self, n=3, tolerance=1, progress=None, homing=False):
        self._block()

    # private
    def _convert_steps(self, v, units):
        if v is not None:
            if units == 'turns':
                v /= float(self.steps_per_turn)
            elif units == 'mm':
                v /= float(self.turns_per_mm * self.steps_per_turn)
        return v

    def _get_steps(self, v, units):
        if units == 'turns':
            v = int(v * self.steps_per_turn)
        elif units == 'mm':
            v = int(v * self.turns_per_mm * self.steps_per_turn)
        return v

    def _set_motor(self, value):
        self._data_position = value

        relative = True
        block = False
        self._move(value, relative, block)

    def _set_var(self, var, val, check_error=True):
        if check_error:
            args = self._check_error()
            if args:
                ecode, estr = args
                self.warning('Existing error ErrorCode={}, Error={}'.format(ecode, estr))

        ret = True
        self.tell('{} {}'.format(var, val))
        if check_error:
            args = self._check_error()
            if args:
                ecode, estr = args
                self.warning('Error setting {}={} ErrorCode={}. Error={}'.format(var, val, ecode, estr))
                ret = False
        return ret

    def _check_error(self):
        eflag = self._get_var('EF')
        if eflag == 1:
            ecode = self._get_var('ER', as_int=False)
            estr = ERROR_MAP.get(ecode, 'See MCode Programming Manual')
            return ecode, estr

    def _get_var(self, c, as_int=True):
        resp = self.ask('PR {}'.format(c))
        if as_int and resp is not None:
            try:
                resp = int(resp)
            except (TypeError, ValueError), e:
                self.debug('invalid var={} response="{}", error={}'.format(c, resp, e))
                resp = None

        self.info('Variable {}={}'.format(c, resp))
        return resp

    def _move(self, pos, relative, block):
        cmd = 'MR' if relative else 'MA'
        self.tell('{} {}'.format(cmd, pos))
        if block:
            self._block()
            self.info('move complete')

    def _moving(self, motion_flag='MV'):
        """
        0= Not Moving
        1= Moving


        motion flags
        MP= moving to position. set after MA or MR
        MV= axis in motion
        """
        resp = self._get_var(motion_flag)
        return resp == 1

    def _block(self):
        while 1:
            if not self._moving():
                break
            time.sleep(0.1)

    def _read_motor_position(self, *args, **kw):
        pos = self._get_var('P')
        return pos

# ============= EOF =============================================
