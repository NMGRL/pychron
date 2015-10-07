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
import time
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.lasers.laser_managers.ethernet_laser_manager import EthernetLaserManager


class ChromiumLaserManager(EthernetLaserManager):
    stage_manager_id = 'chromium.pychron'

    def end_extract(self, *args, **kw):
        self.info('ending extraction. set laser power to 0')
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

    def extract(self, value, units=None, tol=0.1):
        if units is None:
            units = 'watts'

        self.info('set laser output to {} {}'.format(value, units))
        if units == 'watts':
            value = self.calculate_calibrated_power(value)

        resp = self.ask('laser.output {}'.format(value))
        try:
            return abs(float(resp) - value) < tol
        except BaseException:
            pass

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
    def _output_power_changed(self, new):
        self.extract(new, self.units)

    def _set_x(self, v):
        self.ask('stage.moveto {},{},{},{},{},{}'.format(v * 1000, self._y * 1000, self._z * 1000, 10, 10, 0))
        self._moving(v * 1000, self._y * 1000, self._z * 1000)

    def _set_y(self, v):
        self.ask('stage.moveto {},{},{},{},{},{}'.format(self._x * 1000, v * 1000, self._z * 1000, 10, 10, 0))
        self._moving(self._x * 1000, v * 1000, self._z * 1000)

    def _set_z(self, v):
        self.ask('stage.moveto {},{},{},{},{},{}'.format(self._x * 1000, self._y * 1000, v * 1000, 10, 10, 0))
        self._moving(self._x * 1000, self._y * 1000, v * 1000)

    def _move_to_position(self, pos, *args, **kw):
        if isinstance(pos, tuple):
            x, y = pos

        else:
            x, y = self.stage_manager.get_hole_xy(pos)

        z = self.stage_manager.z
        xs = 0
        ys = 0
        zs = 0

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
                    # configuration_dir_name = self.configuration_dir_name,
                    configuration_dir_name=name,
                    parent=self)
        return self._stage_manager_factory(args)

# ============= EOF =============================================
