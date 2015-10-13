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
from traits.api import HasTraits, provides
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.lasers.laser_managers.ethernet_laser_manager import EthernetLaserManager
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager


class ChromiumCO2Manager(EthernetLaserManager):
    stage_manager_id = 'chromium.pychron'
    configuration_dir_name = 'chromium'

    def end_extract(self, *args, **kw):
        self.ask('laser.stop')

        self.info('ending extraction. set laser power to 0')
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

    def fire_laser(self):
        self.info('fire laser')
        self.ask('laser.fire')

    def extract(self, value, units=None, tol=0.1):
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

        self.fire()

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
        x, y, z = 0, 0, 0
        xyz_microns = self.ask('stage.pos?')
        if xyz_microns:
            x, y, z = map(lambda v: float(v) / 1000., xyz_microns.split(','))
        return x, y, z

    def ask(self, cmd, **kw):
        return self._ask('{}\n'.format(cmd), **kw)

    # private
    def _stage_stop_button_fired(self):
        self.ask('stage.stop')
        self.update_position()

    def _fire_laser_button_fired(self):
        if self._firing:
            cmd = 'laser.stop'
        else:
            cmd = 'laser.fire'
        self._firing = not self._firing
        self.ask(cmd)

    def _output_power_changed(self, new):
        self.extract(new, self.units)

    def _set_x(self, v):
        if self._move_enabled:
            self.ask('stage.moveto {},{},{},{},{},{}'.format(v * 1000, self._y * 1000, self._z * 1000, 10, 10, 0))
            self._moving(v * 1000, self._y * 1000, self._z * 1000)

    def _set_y(self, v):
        if self._move_enabled:
            self.ask('stage.moveto {},{},{},{},{},{}'.format(self._x * 1000, v * 1000, self._z * 1000, 10, 10, 0))
            self._moving(self._x * 1000, v * 1000, self._z * 1000)

    def _set_z(self, v):
        if self._move_enabled:
            self.ask('stage.moveto {},{},{},{},{},{}'.format(self._x * 1000, self._y * 1000, v * 1000, 10, 10, 0))
            self._moving(self._x * 1000, self._y * 1000, v * 1000)

    def _move_to_position(self, pos, *args, **kw):
        if isinstance(pos, tuple):
            x, y = pos

        else:
            x, y = self.stage_manager.get_hole_xy(pos)

        z = self._z
        xs = 5000
        ys = 5000
        zs = 100

        xm, ym, zm = x * 1000, y * 1000, z * 1000
        cmd = 'stage.moveto {},{},{},{},{},{}'.format(xm, ym, zm, xs, ys, zs)
        self.info('sending {}'.format(cmd))
        self.ask(cmd)

        return self._moving(xm, ym, zm)

    def _moving(self, xm, ym, zm):
        time.sleep(0.05)

        def cmpfunc(xyz):
            try:
                return not all(map(lambda ab: abs(ab[0] - ab[1]) <= 2,
                                   zip(map(float, xyz.split(',')),
                                       (xm, ym, zm))))
            except ValueError, e:
                print '_moving exception {}'.format(e)

        r = self._block(cmd='stage.pos?\n', cmpfunc=cmpfunc)

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


@provides(ILaserManager)
class ChromiumUVManager(HasTraits):
    def test_connection(self):
        return True

    def bootstrap(self):
        pass

    def bind_preferences(self, *args, **kw):
        pass

    def load(self):
        pass

    def kill(self):
        pass

    def finish_loading(self):
        pass
# ============= EOF =============================================
