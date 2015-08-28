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
from pychron.hardware.pychron_device import EthernetDeviceMixin
from pychron.lasers.laser_managers.base_lase_manager import BaseLaserManager


class ChromiumLaserManager(BaseLaserManager, EthernetDeviceMixin):
    def end_extract(self, *args, **kw):
        self.info('ending extraction. set laser power to 0')
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

    def extract(self, value, units=None, tol=0.1):
        if units is None:
            units = 'watts'

        self.info('set laser output to {} {}'.format(value, units))
        value = self._watts_to_percent(value)
        resp = self.ask('laser.output {}'.format(value))
        try:
            return abs(float(resp) - value) < tol
        except BaseException:
            pass

    def enable_laser(self, **kw):
        self.ask('laser.enable 1')

    def disable_laser(self):
        self.ask('laser.enable 0')

    def get_position(self):
        x, y, z = 0, 0, 0
        xyz_microns = self.ask('stage.pos?')
        if xyz_microns:
            x, y, z = map(lambda v: float(v) / 1000., xyz_microns.split(','))

        return x, y, z

    # private
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
        self._ask(cmd)

        time.sleep(0.5)

        def cmpfunc(xyz):
            try:
                return all(map(lambda a, b: abs(a - b) < 1e5,
                               zip(map(float, xyz.split(',')),
                                   (xm, ym, zm))))
            except ValueError:
                pass

        r = self._block(cmd='stage.pos?', cmpfunc=cmpfunc)

        self.update_position()
        return r

# ============= EOF =============================================
