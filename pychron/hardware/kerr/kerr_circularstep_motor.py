#==============================================================================
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
#==============================================================================

#============= enthought library imports =======================
from traits.api import CInt
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.kerr.kerr_step_motor import KerrStepMotor
import time
from pychron.hardware.core.data_helper import make_bitarray
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


class KerrCircularStepMotor(KerrStepMotor):
    min = CInt
    max = CInt

    def _get_io_bits(self):
        return ['1',  # bit 4
                '1',
                '1',
                '1',
                '0']  # bit 0

    def _home_motor(self, *args, **kw):
        # start moving
        progress = self.progress
        if progress is not None:
            progress = kw['progress']
#             progress.increase_max()
#             progress.change_message('Homing {}'.format(self.name))
#             progress.increment()

#         from threading import Event, Thread
#         signal = Event()
#         t = Thread(target=self.progress_update, args=(progress, signal))
#         t.start()

        #======================================================================
        # step 1. move positive until prox switch is on
        #======================================================================
        # set to max pos
        self._set_motor_position_(self.max, velocity=self.home_velocity)
        # wait until prox switch is on
        self._proximity_move(True, n=1, progress=progress)
        #======================================================================
        # step 2.  reset pos, move positive 55
        #======================================================================
        self.reset_position(motor_off=False)
        moffset = 55
        self._set_motor_position_(moffset, velocity=self.home_velocity)

        #=====================================================================
        # step 3. move 1 step incrementally until home switch set (and proximity not set)
        #=====================================================================
        for i in range(10):
            self._set_motor_position_(i + 1 + moffset, velocity=1)
            time.sleep(0.1)
            lim = self._read_limits()
            if not int(lim[4]) and int(lim[2]):
                break
        #======================================================================
        # step 4. set current position as 0
        #======================================================================
        self.reset_position(motor_off=False)
#         signal.set()
        progress.change_message('{} homing complete'.format(self.name), auto_increment=False)

    def _proximity_move(self, onoff, n=2, progress=None):
        addr = self.address
        cnt = 0
        period = 0.0125
        tc = 0
        totalcnts = 30 / period
        prog = progress
        # poll proximity switch wait for n successes
        while cnt < n and tc < totalcnts:
            time.sleep(period)
            lim = self._get_proximity_limit()

            if (onoff and lim) or  (not onoff and not lim):
                cnt += 1

            if cnt % 10 == 0 and prog:
                prog.change_message('Limit={}, cnt={}'.format(lim, tc), auto_increment=False)

            tc += 1

        # stop moving when proximity limit set
        cmds = [(addr, '1707', 100, 'Stop motor'),  # leave amp on
                (addr, '00', 100, 'Reset Position')]
        self._execute_hex_commands(cmds)
        if tc >= totalcnts:
            self.warning_dialog('Failed Homing motor')

    def _read_limits(self, verbose=False):
        cb = '00001000'
        inb = self.read_status(cb, verbose=False)
        if inb:
            # resp_byte consists of input_byte
            ba = make_bitarray(int(inb[2:-2], 16))
            return ba

    def _get_proximity_limit(self):
        ba = self._read_limits()
        return int(ba[4])

    def _load_home_control_byte(self):
        '''
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
        '''

        return int('00011000', 2)



#============= EOF =============================================
#
#    def _load_trajectory_controlbyte(self):
#        '''
#           control byte
#                7 6 5 4 3 2 1 0
#            97- 1 0 0 1 0 1 1 1
#
#            0=load pos
#            1=load vel
#            2=load acce
#            3=load pwm
#            4=enable servo
#            5=profile mode 0=trap 1=vel
#            6=direction trap mode 0=abs 1=rel vel mode 0=for. 1=back
#            7=start motion now
#
#        '''
#        return '{:02x}'.format(int('10000111', 2))
#
#    def _get_velocity(self):
#        speed = self._velocity #in um/sec
#        res = 0.5
#        steprate = speed / res
#        result = round(steprate / 25)
#        result = min(max(1, result), 250)
#        print 'calcualtes velocity', result
#        return result
