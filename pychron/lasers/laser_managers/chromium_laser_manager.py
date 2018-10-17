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
from pychron.lasers.laser_managers.ethernet_laser_manager import EthernetLaserManager


class ChromiumLaserManager(EthernetLaserManager):
    stage_manager_id = 'chromium.pychron'
    configuration_dir_name = 'chromium'
    _alive = False

    def end_extract(self, *args, **kw):
        self.ask('laser.stop')

        self.info('ending extraction. set laser power to 0')
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

    def fire_laser(self):
        self.info('fire laser')
        self.ask('laser.fire')

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
            time.sleep(1)
            self.fire_laser()

        try:
            return abs(float(resp) - value) < tol
        except BaseException:
            pass

    def set_laser_power(self, v):

        return self.ask('laser.output {}'.format(v))

    def enable_laser(self, **kw):
        # self.ask('laser.enable ON')
        self.enabled = True

    def disable_laser(self):
        self.ask('laser.stop')
        self.enabled = False

    def get_position(self):
        x, y, z = self._x, self._y, self._z
        xyz_microns = self.ask('stage.pos?\n')
        if xyz_microns:
            x, y, z = [float(v) / 1000. for v in xyz_microns.split(',')]
            if self.stage_manager.use_sign_position_correction:
                x = x * self.stage_manager.x_sign
                y = y * self.stage_manager.y_sign
                z = z * self.stage_manager.z_sign
        return x, y, z

    def ask(self, cmd, **kw):
        return self._ask('{}\n'.format(cmd), **kw)

    def linear_move(self, x, y, block=False, *args, **kw):
        self._move_to_position((x, y), block=block)

    def stop(self):
        self.ask('stage.stop')
        self._alive = False
        self.update_position()

    # private
    def _stage_stop_button_fired(self):
        self.stop()

    def _fire_laser_button_fired(self):
        if self._firing:
            cmd = 'laser.stop'
        else:
            cmd = 'laser.fire'
        self._firing = not self._firing
        self.ask(cmd)

    def _output_power_changed(self, new):
        self.extract(new, self.units, fire_laser=False)

    def _set_x(self, v):
        if self._move_enabled:
            self._alive = True
            self.ask('stage.moveto {},{},{},{},{},{}'.format(v * 1000, self._y * 1000, self._z * 1000, 10, 10, 0))
            # self._moving(v * 1000, self._y * 1000, self._z * 1000)
            self._single_axis_moving(v * 1000, 0)

    def _set_y(self, v):
        if self._move_enabled:
            self._alive = True
            self.ask('stage.moveto {},{},{},{},{},{}'.format(self._x * 1000, v * 1000, self._z * 1000, 10, 10, 0))
            # self._moving(self._x * 1000, v * 1000, self._z * 1000)
            self._single_axis_moving(v * 1000, 1)

    def _set_z(self, v):
        if self._move_enabled:
            self._alive = True
            self.ask('stage.moveto {},{},{},{},{},{}'.format(self._x * 1000, self._y * 1000, v * 1000, 10, 10, 0))
            self._single_axis_moving(v * 1000, 2)

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

        self._block(cmd='stage.pos?\n', cmpfunc=cmpfunc)
        time.sleep(0.25)
        self._alive = False
        self.update_position()

    def _move_to_position(self, pos, block=True, *args, **kw):
        if isinstance(pos, tuple):
            x, y = pos

        else:
            x, y = self.stage_manager.get_hole_xy(pos)

        z = self._z
        xs = 5000
        ys = 5000
        zs = 100

        self._alive = True
        self.debug('pos={}, x={}, y={}'.format(pos, x, y))
        xm, ym, zm = self.stage_manager.x_sign * x * 1000, \
                     self.stage_manager.y_sign * y * 1000, \
                     self.stage_manager.z_sign * z * 1000

        cmd = 'stage.moveto {:0.0f},{:0.0f},{:0.0f},{:0.0f},{:0.0f},{:0.0f}'.format(xm, ym, zm, xs, ys, zs)
        self.info('sending {}'.format(cmd))
        self.ask(cmd)

        return self._moving(xm, ym, zm, block)

    def _moving(self, xm, ym, zm, block=True):
        r = True
        if block:
            time.sleep(0.05)

            def cmpfunc(xyz):
                try:
                    if not self._alive:
                        return True

                    # ps = [float(p) for p in xyz.split(',')]
                    ps = csv_to_floats(xyz)
                    # return not all([abs(ab[0] - ab[1]) <= 2 for ab in zip(list(map(float, xyz.split(','))),
                    #                        (xm, ym, zm))])

                    return not all(abs(a - b) <= 10 for a, b in zip(ps, (xm, ym, zm)))
                except ValueError as e:
                    print('_moving exception {}'.format(e))

            r = self._block(cmd='stage.pos?\n', cmpfunc=cmpfunc, period=1)
            self._alive = False
            self.update_position()
        return r

    def _stage_manager_default(self):

        name = 'chromium'
        args = dict(name='stage',
                    configuration_name='stage',
                    configuration_dir_name=name,
                    parent=self)
        return self._stage_manager_factory(args)

    def _stage_manager_factory(self, args):
        from pychron.lasers.stage_managers.chromium_stage_manager import ChromiumStageManager

        self.stage_args = args

        klass = ChromiumStageManager
        sm = klass(**args)
        sm.id = self.stage_manager_id

        return sm

    def _pattern_executor_default(self):
        from pychron.lasers.pattern.pattern_executor import PatternExecutor

        pm = PatternExecutor(application=self.application,
                             controller=self,
                             laser_manager=self)
        return pm


class ChromiumCO2Manager(ChromiumLaserManager):
    pass


class ChromiumDiodeManager(ChromiumLaserManager):
    pass

# ============= EOF =============================================
