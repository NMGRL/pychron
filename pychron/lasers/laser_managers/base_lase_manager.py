# ===============================================================================
# Copyright 2013 Jake Ross
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

import os
import time

# ============= enthought library imports =======================
from traits.api import Instance, Event, Bool, Any, Property, Float, provides

from pychron.core.helpers.filetools import list_directory
from pychron.core.helpers.strtools import to_bool, csv_to_floats
from pychron.hardware.meter_calibration import MeterCalibration
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.managers.manager import Manager
from pychron.paths import paths


@provides(ILaserManager)
class BaseLaserManager(Manager):
    # implements(ILaserManager)
    # provides(ILaserManager)
    pattern_executor = Instance(
        "pychron.lasers.pattern.pattern_executor.PatternExecutor"
    )
    use_video = Bool(False)

    enable = Event
    enable_label = Property(depends_on="enabled")
    # enabled_led = Instance('pychron.core.ui.led_editor.LED', ())
    enabled = Bool(False)

    stage_manager = Instance("pychron.lasers.stage_managers.stage_manager.StageManager")
    stage_controller_klass = "Newport"

    requested_power = Any
    status_text = Property(depends_on="_requested_power, enabled")
    pulse = Any
    laser_controller = Any
    mode = "normal"

    use_calibrated_power = Bool(True)
    requested_power = Property(Float, depends_on="_requested_power")
    units = Property(depends_on="use_calibrated_power")
    _requested_power = Float
    _calibrated_power = None
    _cancel_blocking = False

    def bind_preferences(self, prefid):
        pass

    def opened(self):
        pass

    def test_connection(self):
        if self.mode == "client":
            return self._test_connection()
        else:
            return True, None

    # def initialize_video(self):
    #     if self.use_video:
    #         self.stage_manager.initialize_video()

    def update_position(self):
        self.debug("update position")
        pos = self.get_position()
        self.debug("got position {}".format(pos))
        if pos:
            if self.stage_manager:
                self.stage_manager.trait_set(
                    **dict(
                        list(zip(("_x_position", "_y_position", "_z_position"), pos))
                    )
                )
            return pos

    def wake(self):
        from pychron.core.ui.gui import wake_screen

        wake_screen()

    def is_ready(self):
        return True

    def take_snapshot(self, *args, **kw):
        pass

    def end_extract(self, *args, **kw):
        self.disable_laser()

    def extract(self, *args, **kw):
        pass

    def prepare(self, *args, **kw):
        pass

    def get_motor_lock(self, name, value):
        pass

    def set_motor(self, *args, **kw):
        pass

    def get_motor(self, name):
        pass

    def enable_device(self, **kw):
        return self.enable_laser(**kw)

    def disable_device(self):
        self.disable_laser()

    def enable_laser(self, **kw):
        pass

    def set_laser_power(self, *args, **kw):
        pass

    def disable_laser(self):
        pass

    def get_pyrometer_temperature(self):
        pass

    def get_grain_polygon_blob(self):
        pass

    def get_pattern_names(self):
        p = paths.pattern_dir
        extension = ".lp,.txt"
        patterns = list_directory(p, extension)
        return [
            "",
        ] + patterns

    def execute_pattern(
        self, name=None, duration=None, block=False, lase=False, thread_safe=True
    ):
        # if not self.stage_manager.temp_hole:
        #     self.information_dialog('Need to specify a hole')
        #     return

        pm = self.pattern_executor
        self.debug(
            "execute pattern {}, duration=duration, block={}, lase={}".format(
                name, duration, block, lase
            )
        )
        if pm.load_pattern(name):
            pm.set_stage_values(self.stage_manager)

            if lase:
                pm.pattern.disable_at_end = True
                if not self.enable_laser():
                    return
                self.set_laser_power(self.pulse.power, verbose=True)

            pm.execute(block, duration, thread_safe=thread_safe)

    def get_brightness(self, **kw):
        return 0

    def stop_pattern(self):
        if self.pattern_executor:
            self.pattern_executor.stop()

    def isPatterning(self):
        if self.pattern_executor:
            return self.pattern_executor.isPatterning()

    def move_to_position(self, pos, *args, **kw):
        if not isinstance(pos, list):
            pos = [pos]

        for p in pos:
            self._move_to_position(p, *args, **kw)

        return True

    def trace_path(self, *args, **kw):
        pass

    def drill_point(self, *args, **kw):
        pass

    def set_motors_for_point(self, pt):
        pass

    def get_achieved_output(self):
        pass

    def get_response_blob(self):
        pass

    def get_output_blob(self):
        pass

    def set_response_recorder_period(self, v):
        pass

    def start_response_recorder(self):
        pass

    def stop_response_recorder(self):
        pass

    def calculate_calibrated_power(self, request, calibration="watts", verbose=True):
        mc = self._calibration_factory(calibration)
        if verbose:
            self.info(
                "using power coefficients  (e.g. ax2+bx+c) {}".format(mc.print_string())
            )
        return mc.get_input(request)

    def get_tray(self):
        sm = self.stage_manager
        if sm:
            return sm.stage_map_name

    # private
    def _move_to_position(self, *args, **kw):
        pass

    def _get_hole_xy(self, pos):
        sm = self.stage_manager
        if isinstance(pos, tuple):
            x, y = pos

        else:
            try:
                x, y = sm.get_hole_xy(pos)
            except ValueError:
                self.warning_dialog(
                    "Invalid position {} for {}".format(pos, sm.stage_map_name)
                )
                return
        return x, y

    def _block(
        self,
        cmd="GetDriveMoving",
        cmpfunc=None,
        period=0.25,
        position_callback=None,
        nsuccess=2,
        timeout=50,
    ):
        ask = self._ask

        cnt = 0
        self._cancel_blocking = False
        if cmpfunc is None:
            cmpfunc = to_bool

        st = time.time()
        while 1:
            if cnt > nsuccess:
                break

            if time.time() - st > timeout:
                break

            if self._cancel_blocking:
                break

            time.sleep(period)
            resp = ask(cmd)

            if self.communicator.simulation:
                resp = "False"

            if resp is not None:
                try:
                    if not cmpfunc(resp):
                        cnt += 1
                except (ValueError, TypeError) as e:
                    print("_blocking exception {}".format(e))
                    cnt = 0

                if position_callback:
                    if self.communicator.simulation:
                        x, y, z = cnt / 3.0, cnt / 3.0, 0
                        position_callback(x, y, z)
                    else:
                        xyz = self.get_position()
                        if xyz:
                            position_callback(*xyz)
            else:
                cnt = 0

        state = cnt >= nsuccess
        if state:
            self.info("Block completed")
        else:
            if self._cancel_blocking:
                self.info("Block failed. canceled by user")
            else:
                self.warning("Block failed. timeout after {}s".format(timeout))

        return state

    def _calibration_factory(self, calibration):
        coeffs = None
        nmapping = False
        if calibration == "watts":
            path = os.path.join(
                paths.device_dir, self.configuration_dir_name, "calibrated_power.cfg"
            )
            if os.path.isfile(path):
                config = self.get_configuration(path=path)
                coeffs, nmapping = self._get_watt_calibration(config)

        if coeffs is None:
            coeffs = [1, 0]

        return MeterCalibration(coeffs, normal_mapping=bool(nmapping))

    def _get_watt_calibration(self, config):
        coeffs = [1, 0]
        nmapping = False
        section = "PowerOutput"
        if config.has_section(section):
            cs = config.get(section, "coefficients")
            try:
                coeffs = csv_to_floats(cs)
            except ValueError:
                self.warning_dialog("Invalid power calibration {}".format(cs))
                return

            if config.has_option(section, "normal_mapping"):
                nmapping = config.getboolean(section, "normal_mapping")

        return coeffs, nmapping

    # ===============================================================================
    # getter/setters
    # ===============================================================================
    def _get_status_text(self):
        s = "Laser OFF"
        if self.enabled:
            s = "Laser Enabled"
            if self._requested_power:
                s = "Laser ON {:05.2f}{}".format(self._requested_power, self.units)

        return s

    def _get_enable_label(self):
        """ """
        return "DISABLE" if self.enabled else "ENABLE"

    def _get_calibrated_power(self, power, use_calibration=True, verbose=True):
        if power:
            if self.use_calibrated_power and use_calibration:
                power = max(0, self.calculate_calibrated_power(power, verbose=verbose))
        return power

    def _get_requested_power(self):
        return self._requested_power

    def _get_units(self):
        return "(W)" if self.use_calibrated_power else "(%)"

    # ===============================================================================
    # handlers
    # ===============================================================================
    # def _enabled_changed(self):
    #     if self.enabled:
    #         self.enabled_led.set_state('green')
    #     else:
    #         self.enabled_led.set_state('red')

    def _use_video_changed(self):
        if not self.use_video:
            try:
                self.stage_manager.video.close()
            except AttributeError as e:
                print("use video 1", e)

        try:
            sm = self._stage_manager_factory(self.stage_args)

            sm.stage_controller = self.stage_manager.stage_controller
            sm.stage_controller.parent = sm
            if self.plugin_id:
                sm.bind_preferences(self.plugin_id)
            #             sm.visualizer = self.stage_manager.visualizer

            sm.load()

            self.stage_manager = sm
        except AttributeError as e:
            print("use video 2", e)

    def _stage_manager_factory(self, args):
        self.stage_args = args
        if self.use_video:
            from pychron.lasers.stage_managers.video_stage_manager import (
                VideoStageManager,
            )

            klass = VideoStageManager
        else:
            from pychron.lasers.stage_managers.stage_manager import StageManager

            klass = StageManager

        args["parent"] = self
        sm = klass(**args)
        sm.id = self.stage_manager_id
        return sm

    # defaults
    # def _enabled_led_default(self):
    #     from pychron.core.ui.led_editor import LED
    #     return LED()

    def _pattern_executor_default(self):
        from pychron.lasers.pattern.pattern_executor import PatternExecutor

        controller = None
        if hasattr(self, "stage_manager"):
            controller = self.stage_manager.stage_controller

        pm = PatternExecutor(
            application=self.application, controller=controller, laser_manager=self
        )
        self._pattern_executor_init_hook(pm)
        return pm

    def _pattern_executor_init_hook(self, pm):
        pass

    def _stage_manager_default(self):
        """ """
        args = dict(
            name="stage",
            configuration_name="stage",
            configuration_dir_name=self.configuration_dir_name,
            stage_controller_klass=self.stage_controller_klass,
            parent=self,
        )

        return self._stage_manager_factory(args)


# ============= EOF =============================================
