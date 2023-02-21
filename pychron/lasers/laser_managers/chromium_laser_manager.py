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
from pychron.experiment.utilities.position_regex import SCAN_REGEX
from pychron.lasers.laser_managers.ethernet_laser_manager import EthernetLaserManager


class ChromiumLaserManager(EthernetLaserManager):
    stage_manager_id = "chromium.pychron"
    configuration_dir_name = "chromium"
    _alive = False

    def setup_communicator(self):
        com = super(ChromiumLaserManager, self).setup_communicator(
            write_terminator="\r\n", read_terminator="\r\n"
        )
        if self.communicator:
            self.communicator.report()

        return com

    def set_tray(self, t):
        if self.stage_manager:
            self.stage_manager.stage_map_name = t

    def end_extract(self, *args, **kw):
        self._ask("laser.stop")

        self.info("ending extraction. set laser power to 0")
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

    def fire_laser(self):
        self.info("fire laser")
        self._ask("laser.fire")

    def extract(self, value, units=None, tol=0.1, fire_laser=True, **kw):
        if units is None:
            units = "watts"

        self.info("set laser output to {} {}".format(value, units))
        if units == "watts":
            ovalue = value
            value = self.calculate_calibrated_power(value)
            if value < 0:
                self.warning(
                    "Consider changing you calibration curve. "
                    "{} watts converted to {}%. % must be positive".format(
                        ovalue, value
                    )
                )
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
        return self._ask("laser.output {}".format(v))

    def enable_laser(self, **kw):
        # self.ask('laser.enable ON')
        self.enabled = True

    def disable_laser(self):
        self._ask("laser.stop")
        self.enabled = False

    def get_position(self):
        x, y, z = self._x, self._y, self._z
        xyz_microns = self._ask("stage.pos?")
        if xyz_microns:
            x, y, z = [float(v) / 1000.0 for v in xyz_microns.split(",")]
            if self.stage_manager.use_sign_position_correction:
                x = x * self.stage_manager.x_sign
                y = y * self.stage_manager.y_sign
                z = z * self.stage_manager.z_sign
            return x, y, z

    def linear_move(self, x, y, block=False, *args, **kw):
        self._move_to_position((x, y), block=block)

    def stop(self):
        self._ask("stage.stop")
        self._alive = False
        self.update_position()

    # private
    def _stage_stop_button_fired(self):
        self.stop()

    def _fire_laser_button_fired(self):
        if self._firing:
            cmd = "laser.stop"
        else:
            cmd = "laser.fire"
        self._firing = not self._firing
        self._ask(cmd)

    def _output_power_changed(self, new):
        self.extract(new, self.units, fire_laser=False)

    def _set_x(self, v):
        if self._move_enabled:
            self._alive = True
            self._ask(
                "stage.moveto {},{},{},{},{},{}".format(
                    v * 1000, self._y * 1000, self._z * 1000, 10, 10, 0
                )
            )
            self._single_axis_moving(v * 1000, 0)

    def _set_y(self, v):
        if self._move_enabled:
            self._alive = True
            self._ask(
                "stage.moveto {},{},{},{},{},{}".format(
                    self._x * 1000, v * 1000, self._z * 1000, 10, 10, 0
                )
            )
            self._single_axis_moving(v * 1000, 1)

    def _set_z(self, v):
        if self._move_enabled:
            self._alive = True
            self._ask(
                "stage.moveto {},{},{},{},{},{}".format(
                    self._x * 1000, self._y * 1000, v * 1000, 10, 10, 0
                )
            )
            self._single_axis_moving(v * 1000, 2)

    def _single_axis_moving(self, v, axis):
        def cmpfunc(xyz):
            try:
                if not self._alive:
                    return True

                pos = float(xyz.split(",")[axis])
                return abs(pos - v) > 2
            except ValueError as e:
                print("_moving exception {}".format(e))

        self._block(cmd="stage.pos?", cmpfunc=cmpfunc)
        time.sleep(0.25)
        self._alive = False
        self.update_position()

    def _move_to_position(self, pos, block=True, *args, **kw):
        sm = self.stage_manager
        try:
            x, y = self._get_hole_xy(pos)
        except ValueError:
            return

        z = self._z
        xs = 5000
        ys = 5000
        zs = 100

        self._alive = True
        self.debug("pos={}, x={}, y={}".format(pos, x, y))

        xm = x * 1000
        ym = y * 1000
        zm = z * 1000
        if sm.use_sign_position_correction:
            xm *= sm.x_sign
            ym *= sm.y_sign
            zm *= sm.z_sign

        cmd = "stage.moveto {:0.0f},{:0.0f},{:0.0f},{:0.0f},{:0.0f},{:0.0f}".format(
            xm, ym, zm, xs, ys, zs
        )
        self.info("sending {}".format(cmd))
        self._ask(cmd)

        time.sleep(1)
        return self._moving(xm, ym, zm, block)

    def _moving(self, xm, ym, zm, block=True):
        r = True
        if block:
            time.sleep(0.05)

            def cmpfunc(xyz):
                try:
                    if not self._alive:
                        return True
                    ps = csv_to_floats(xyz)

                    return not all(abs(a - b) <= 10 for a, b in zip(ps, (xm, ym, zm)))
                except ValueError as e:
                    print("_moving exception {}".format(e))

            r = self._block(cmd="stage.pos?", cmpfunc=cmpfunc, period=1)
            self._alive = False
            self.update_position()
        return r

    def _stage_manager_factory(self, args):
        from pychron.lasers.stage_managers.chromium_stage_manager import (
            ChromiumStageManager,
        )

        self.stage_args = args

        klass = ChromiumStageManager
        sm = klass(**args)
        sm.id = self.stage_manager_id

        return sm

    def _pattern_executor_default(self):
        from pychron.lasers.pattern.pattern_executor import PatternExecutor

        pm = PatternExecutor(
            application=self.application, controller=self, laser_manager=self
        )
        return pm


class ChromiumCO2Manager(ChromiumLaserManager):
    pass


class ChromiumDiodeManager(ChromiumLaserManager):
    pass


def scans(cmd):
    return "Scans.{}".format(cmd)


class ChromiumUVManager(ChromiumLaserManager):
    configuration_dir_name = "chromium_uv"
    _active_scan = None

    def active_scan_cmd(self, cmd):
        return scans("{} {}".format(cmd, self._active_scan))

    def ask_active_scan(self, cmd):
        return self._ask(self.active_scan_cmd(cmd))

    def _opened_hook(self):
        self._ask(scans("Status_Verbosity 1"))

    def warmup(self, block=None):
        if self._active_scan:
            self._warmed = True
            self.ask_active_scan("Run")

            if block:

                def func(r):
                    return r.lower() != "running: warming up laser..."

                self._block(cmd=scans("Status?"), cmpfunc=func, timeout=120)

    def extract(self, *args, **kw):
        if self._active_scan:
            if not self._warmed:
                self.ask_active_scan("Run")

            def func(r):
                return str(r).strip().lower() != "idle: idle"

            self._block(
                cmd=scans("Status?"), cmpfunc=func, timeout=kw.get("block", 300) or 300
            )
            self._warmed = False
            return True
        else:
            return super(ChromiumUVManager, self).extract(*args, **kw)

    def _move_to_position(self, pos, *args, **kw):
        # if position is a valid predefined scan list use it
        # otherwise interpret as normal hole/x,y pos

        scan_id = self._get_scan_id(pos)
        if scan_id:
            self._active_scan = scan_id
            self.ask_active_scan("MoveTo")

            def func(r):
                return not bool(int(r))

            self._block(cmd=self.active_scan_cmd("InPos?"), cmpfunc=func)

        else:
            self._active_scan = None
            return super(ChromiumUVManager, self)._move_to_position(pos, *args, **kw)

    def disable_laser(self):
        self._ask(scans("Stop"))
        super(ChromiumUVManager, self).disable_laser()

    def _get_scan_id(self, pos):
        m = SCAN_REGEX[0].match(pos)
        if m:
            return int(m.group("id")[1:])
        return


# ============= EOF =============================================
