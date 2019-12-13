# ===============================================================================
# Copyright 2015 Jake Ross
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
# ============= standard library imports ========================
import time

# ============= local library imports  ==========================
from pychron.core.helpers.strtools import csv_to_floats
from pychron.lasers.laser_managers.serial_laser_manager import SerialLaserManager


class AblationCO2Manager(SerialLaserManager):
    stage_manager_id = 'ablation.pychron'
    configuration_dir_name = 'ablation'
    _alive = False
    read_delay = 25
    
    def _test_connection_hook(self):
        re = self._ask('GetVersion')
        self.connected = bool(re)

    def end_extract(self, *args, **kw):

        self.info('ending extraction. set laser power to 0')
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

        self.disable_laser()

    def fire_laser(self):
        self.info('fire laser')
        self._ask('SetLaserOn 1')

    def extract(self, value, units=None, tol=0.1, fire_laser=True):
        if units is None:
            units = 'watts'

        self.info('set laser output to {} {}'.format(value, units))
        if units == 'watts':
            ovalue = value
            value = self.calculate_calibrated_power(value)
            if value < 0:
                self.warning('Consider changing you calibration curve. '
                             '{} watts converted to {}%. % must be positive'.format(ovalue, value))
                value = 0

        resp = self.set_laser_power(value)
        if fire_laser:
            time.slVaeep(1)
            self.fire_laser()

        try:
            return abs(float(resp) - value) < tol
        except BaseException:
            pass

    def set_laser_power(self, v):
        self.debug('setting laser output to {}'.format(v))
        return self._ask('SetLaserOutput {}'.format(v))

    def enable_laser(self, **kw):
        # self._ask('laser.enable ON')
        self.info('enabling laser')
        self._ask('SetLaserFireMode 3')  # 3= continuous wave
        #self._ask('SetLaserOn 1')
        self.enabled = True

    def disable_laser(self):
        self.info('disabling laser')
        self.set_laser_power(0)
        self._ask('SetLaserOn 0')
        self.enabled = False

    def get_position(self):
        x, y, z = self._x, self._y, self._z
        xyz = self._ask('ReadPosition')
        if xyz:
            try:
                x, y, z = [float(v) for v in xyz.split(',')]
                if self.stage_manager.use_sign_position_correction:
                    x = x * self.stage_manager.x_sign
                    y = y * self.stage_manager.y_sign
                    z = z * self.stage_manager.z_sign
            except ValueError:
                self.warning('failed parsing position: {}'.format(xyz))
                
        return x, y, z

    # def ask(self, cmd, **kw):
    #     return self._ask('{}\r'.format(cmd), **kw)

    def linear_move(self, x, y, block=False, *args, **kw):
        self._move_to_position((x, y), block=block)

    def stop(self):
        # self._ask('stage.stop')
        self._alive = False
        self.update_position()

    # private
    def _stage_stop_button_fired(self):
        self.stop()

    def _fire_laser_button_fired(self):
        if self._firing:
            cmd = 0
        else:
            cmd = 1
        self._firing = not self._firing
        self._ask('SetLaserOn {}'.format(cmd))

    def _output_power_changed(self, new):
        self.extract(new, self.units, fire_laser=False)

    def _set_x(self, v):
        if self._move_enabled and v!=self._x:
            self._alive = True
            self._ask('SetPosition {:0.3f},{:0.3f},{:0.3f}'.format(v, self._y, self._z))
            self._single_axis_moving(v, 0)

    def _set_y(self, v):
        if self._move_enabled and v!=self._y:
            self._alive = True
            self._ask('SetPosition {:0.3f},{:0.3f},{:0.3f}'.format(self._x, v, self._z))
            self._single_axis_moving(v, 1)

    def _set_z(self, v):
        if self._move_enabled and v!=self._z:
            self._alive = True
            self._ask('SetPosition {:0.3f},{:0.3f},{:0.3f}'.format(self._x, self._y, v))
            self._single_axis_moving(v, 2)

    def _single_axis_moving(self, v, axis):
        def cmpfunc(xyz):
            try:
                if not self._alive:
                    return True

                # pos =[float(p) for p in xyz.split(','))[axis]
                pos = float(xyz.split(',')[axis])

                return abs(pos - v) > 2
                # print map(lambda ab: abs(ab[0] - ab[1]) <= 2,
                #           zip(map(float, xyz.split(',')),
                #               (xm, ym, zm)))

                # return not all(map(lambda ab: abs(ab[0] - ab[1]) <= 2,
                #                    zip(map(float, xyz.split(',')),
                #                        (xm, ym, zm))))
            except ValueError as e:
                print('_moving exception {}'.format(e))

        self._block(cmd='ReadPosition', cmpfunc=cmpfunc)
        time.sleep(0.25)
        self._alive = False
        self.update_position()

    def _move_to_position(self, pos, autocenter=False, block=True, *args, **kw):
        sm = self.stage_manager
        try:
            x, y = self._get_hole_xy(pos)
        except ValueError:
            return

        z = self._z
        #xs = 5000
        #ys = 5000
        #zs = 100

        self._alive = True
        self.debug('pos={}, x={}, y={}'.format(pos, x, y))

        if sm.use_sign_position_correction:
            x *= sm.x_sign
            y *= sm.y_sign
            z *= sm.z_sign

        cmd = 'SetPosition {:0.3f},{:0.3f},{:0.3f}'.format(x, y, z)
        self.info('sending {}'.format(cmd))
        self._ask(cmd)

        time.sleep(1)
        return self._moving(x, y, z, block)

    def _moving(self, xm, ym, zm, block=True):
        r = True
        if block:
            time.sleep(0.5)

            def cmpfunc(xyz):
                try:
                    if not self._alive:
                        return True

                    # ps = [float(p) for p in xyz.split(',')]
                    ps = csv_to_floats(xyz)
                    # return not all([abs(ab[0] - ab[1]) <= 2 for ab in zip(list(map(float, xyz.split(','))),
                    #                        (xm, ym, zm))])

                    return not all(abs(a - b) <= 0.01 for a, b in zip(ps, (xm, ym, zm)))
                except ValueError as e:
                    print('_moving exception {}'.format(e))

            r = self._block(cmd='ReadPosition', cmpfunc=cmpfunc, period=1)
            self._alive = False
            time.sleep(0.5)
            self.update_position()
        return r

    def _stage_manager_default(self):

        name = 'ablation'
        args = dict(name='stage',
                    configuration_name='stage',
                    configuration_dir_name=name,
                    parent=self)
        return self._stage_manager_factory(args)

    def _stage_manager_factory(self, args):
        from pychron.lasers.stage_managers.ablation_stage_manager import AblationStageManager

        self.stage_args = args

        klass = AblationStageManager
        sm = klass(**args)
        sm.id = self.stage_manager_id

        return sm

    def _pattern_executor_default(self):
        from pychron.lasers.pattern.pattern_executor import PatternExecutor

        pm = PatternExecutor(application=self.application,
                             controller=self,
                             laser_manager=self)
        return pm

# ============= EOF =============================================
