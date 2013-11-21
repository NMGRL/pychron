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
# from traits.api import HasTraits, on_trait_change, Str, Int, Float, Button
# from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================

#============= local library imports  ==========================
import time

from aerotech_axis import AerotechAxis
from pychron.hardware.motion_controller import MotionController
from pychron.hardware.core.data_helper import make_bitarray


ACK = chr(6)
NAK = chr(15)
EOS = chr(10)


class AerotechMotionController(MotionController):
    def initialize(self, *args, **kw):
        '''
        '''
        self._communicator.write_terminator = None
        self.tell('##')
        self._communicator.write_terminator = chr(13)
        self._communicator.read_delay = 25
        self.enable()
#        self.home()
#        for a in self.axes.itervalues():
#            a.load_parameters()

        return True

    def load_additional_args(self, config):
        '''

        '''
        self.axes_factory()
        return True

    def xy_swapped(self):
        if self.axes.has_key('y'):
            return self.axes.keys().index('y') == 0

    def linear_move(self, x, y, sign_correct=True, block=False, velocity=None,
                    set_stage=True,
                    buf=None,
                    mode='relative', **kw):
        '''
            unidex 511 5-55 Linear
        '''
        errx = self._validate(x, 'x', cur=self._x_position)
        erry = self._validate(y, 'y', cur=self._y_position)
        if errx is None and erry is None:
            return 'invalid position {},{}'.format(x, y)
        if set_stage:
            self.parent.canvas.set_desired_position(x, y)
        self._x_position = x
        self._y_position = y
        if mode == 'absolute':
            px, py = 0, 0
        else:
            px = self.get_current_position('x')
            py = self.get_current_position('y')

        nx = x - px
        ny = y - py
        if sign_correct:
            nx = self._sign_correct(nx, 'x', ratio=False)
            ny = self._sign_correct(ny, 'y', ratio=False)

        x = self.axes['x']
        y = self.axes['y']

        if velocity is not None:
            xv = yv = velocity
        else:
            xv = x.velocity
#            yv=y.velocity

#        if abs(nx)>1:
#            xv=xv*0.5
#        if abs(nx)>1:
#            yv=yv*0.5

        if self.xy_swapped():
            cmd = 'ILI X{} Y{} F{}'.format(ny, nx, xv)
        else:
            cmd = 'ILI X{} Y{} F{}'.format(nx, ny, xv)

        if buf:
            buf.append(cmd)
        else:
            self.ask(cmd, handshake_only=True)
            if block:
                self.timer = self.timer_factory()
                self.block()
            elif set_stage:
                self.parent.canvas.set_stage_position(self._x_position, self._y_position)

    def set_single_axis_motion_parameters(self, axis=None, pdict=None):
        if pdict is not None:
            key = pdict['key']
            self.axes[key].velocity = pdict['velocity']

    def single_axis_move(self, key, value, block=False, **kw):
        '''
            unidex 511 5-50 Index
        '''
        nkey = self._get_axis_name(key)
        axis = self.axes[nkey]
        name = axis.name.upper()
        cp = self.get_current_position(key)
        if self._validate(value, nkey, cp) is not None:
            setattr(self, '_{}_position'.format(key), value)
            nv = value - cp
            #            if key == 'x':
            #                x = value
            #                y = self._y_position
            #                o = self._x_position
            #            else:
            #                x = self._x_position
            #                y = value
            #                o = self._y_position
            x = self._x_position
            y = self._y_position
            self.parent.canvas.set_stage_position(x, y)

            nv = self._sign_correct(nv, key, ratio=False)
            cmd = 'IIN {}{} {}F{}'.format(name, nv, name, axis.velocity)

            if name == 'Z':
                func = self._z_inprogress_update
            else:
                func = self._inprogress_update

            self.ask(cmd, handshake_only=True)

            self.timer = self.timer_factory(func=func)
            if block:
                self.block()
            else:
                if name == 'Z':
                    self.z_progress = value

                self.parent.canvas.set_stage_position(x, y)

                #    def enqueue_move(self, x, y, v):
                #        if self.xy_swapped():
                #            cmd = 'LI X{} Y{} F{}'.format(y, x, v)
                #        else:
                #            cmd = 'LI X{} Y{} F{}'.format(x, y, v)
                #        self.ask(cmd, handshake_only=True)

    def start_command_buffer(self):
        self.hold(True)

    def end_command_buffer(self):
        self.hold(False)

#     def execute_command_buffer(self):
#         self.trigger()
#         self.timer = self.timer_factory()
#         self.block()
#
#     def execute_command_buffer(self, buf):
#         if isinstance(buf, (list, tuple)):
#             buf = '\n'.join(buf)
#         self.ask(buf, handshake_only=True)


    def hold(self, onoff):
        cmd = 'HD{}'.format(int(onoff))
        self.ask(cmd)

    def trigger(self):
        cmd = 'TR'
        self.ask(cmd)

    def set_program_mode(self, mode):
        '''
            using metric units
        '''
        cmd = 'IPR ME'
        v = 'AB' if mode == 'absolute' else 'IN'
        cmd = '{} {}'.format(cmd, v)
        self.ask(cmd)

    def set_smooth_transitions(self, smooth):
        '''
            unidex 511 5-57 Velocity mode
        '''

        cmd = 'IVE'
        v = 'ON' if smooth else 'OFF'
        cmd = '{} {}'.format(cmd, v)
        self.ask(cmd, handshake_only=True)
#    def _relative_move(self, axes, values):
#        '''
#        '''
#
#        cmd = 'INDEX'
#
#        cmd = self._build_command(cmd, axes, values=values)
#        resp = self.ask(cmd)
#        return self._parse_response(resp)

    def _moving_(self, *args, **kw):
        '''
            unidex 511 6-12 Serial Pol
        '''
        cmd = 'Q'
        sb = self.ask(cmd, verbose=False)
        if sb is not None:
        # cover status bit to binstr
            b = make_bitarray(int(sb))
            return int(b[2])

    def get_xy(self):
        return self.get_current_position('x'), self.get_current_position('y')

    def get_current_position(self, axis, verbose=False):
        '''
            unidex 511 6-11 Axis Positions
        '''
        naxis = self._get_axis_name(axis)

        cmd = 'P{}'.format(naxis)
        pos = self.ask(cmd, verbose=verbose)
        if pos is not None:
            pos = float(pos)
            pos = self._sign_correct(pos, axis)
#            setattr(self, '_{}_position'.format(axis), pos)
        else:
            pos = 0

        return pos

    def enable(self, axes=None):
        '''
            unidex 511 5-39 Enable
        '''

        cmd = 'IEN'
        axes = self._get_axes_name_list(axes)
        cmd = '{} {}'.format(cmd, axes)
        resp = self.ask(cmd, handshake_only=True)

    def _get_axes_name_list(self, axes):
        if axes is None:
            axes = self.axes.keys()
        axes = map(str.upper, axes)
        return ' '.join(axes)
#    def disable(self):
#        '''
#        '''
#
#        cmd = 'DI'
#
#        axes = ['X', 'Y', 'Z']
#        axes = ' '.join(axes)
#        cmd = self._build_command(cmd, axes)
#        self.tell(cmd)
#        #resp=self.ask(cmd)
#        #return self._parse_response(resp)
    def define_home(self, axes=None):
        '''
            unidex 511 5-83 Software
        '''
        cmd = 'ISO HOME'
        axes = self._get_axes_name_list(axes)

        cmd = '{} {}'.format(cmd, axes)
        resp = self.ask(cmd, handshake_only=True)

    def home(self, axes=None):
        '''
            unidex 511 5-48 home
        '''
        cmd = 'IHO'
        axes = self._get_axes_name_list(axes)

        cmd = '{} {}'.format(cmd, axes)
        self.ask(cmd, handshake_only=True)
        time.sleep(1)
        self.block()
        time.sleep(1)
        self.linear_move(25, 25, sign_correct=False)
        time.sleep(1)
        self.block()
        self.define_home()

    def stop(self, **kw):
        '''
            unidex 511 5-13 Abort
        '''
        cmd = 'IAB'
        self.ask(cmd, handshake_only=True)

    def ask(self, cmd, **kw):
        return super(AerotechMotionController, self).ask(cmd, handshake=[ACK, NAK], **kw)

    def _axis_factory(self, path, **kw):
        '''
        '''
        a = AerotechAxis(parent=self, **kw)
        p = a.load(path)
        return a

    def _get_axis_name(self, axis):
#        print self.axes.keys(),self.axes.keys().index('y')
        if axis in ('x', 'y'):
            if self.xy_swapped():
#            if self.axes.keys().index('y') == 0:
                if axis == 'y':
                    axis = 'x'
                else:
                    axis = 'y'
        return axis
# if __name__ == '__main__':
#    amc = Aero


#============= EOF ====================================

