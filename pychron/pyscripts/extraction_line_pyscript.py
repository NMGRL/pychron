# ===============================================================================
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
# ===============================================================================

import inspect
import re
import time
from threading import Event
from threading import Thread

from traits.api import List, Dict

from pychron.core.ramper import Ramper
from pychron.external_pipette.protocol import IPipetteManager
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.hardware.core.exceptions import TimeoutError
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.pychron_constants import (
    EXTRACTION_COLOR,
    LINE_STR,
    NULL_STR,
    EL_PROTOCOL,
    PATTERN,
    POSTCLEANUP,
    PRECLEANUP,
    CLEANUP,
    DURATION,
    CRYO_TEMP,
)
from pychron.pyscripts.context_managers import (
    RecordingCTX,
    LightingCTX,
    GrainPolygonCTX,
)
from pychron.pyscripts.decorators import verbose_skip, makeRegistry, calculate_duration
from pychron.pyscripts.valve_pyscript import ValvePyScript

COMPRE = re.compile(r"[A-Za-z]*")

# make a registry to hold all the commands exposed by ExtractionPyScript
# used when building the context
# see PyScript.get_context and get_command_register
command_register = makeRegistry()


class ExtractionPyScript(ValvePyScript):
    """
    The ExtractionPyScript is used to program the extraction and gettering of
    sample gas.
    """

    automated_run = None

    _resource_flag = None
    info_color = EXTRACTION_COLOR
    snapshots = List
    videos = List
    extraction_context = Dict

    _extraction_positions = List
    _grain_polygons = List

    def set_load_identifier(self, v):
        self.setup_context(load_identifier=v)

    def set_run_identifier(self, v):
        self.setup_context(run_identifier=v)

    def get_extraction_positions(self, clear=True):
        """
        Returns a list of x,y,z tuples
        each tuple represents where the extraction occurred

        if clear is True (default) ``self._extraction_positions`` set to an empty list

        :return: list of x,y,z tuples
        :rtype: list of tuples

        """
        ret = self._extraction_positions
        if clear:
            self._extraction_positions = []

        return ret

    def get_grain_polygons(self):
        m = self._grain_polygons
        if not m:
            m = self._extraction_action(("get_grain_polygon_blob", (), {}))
        return m

    def get_cryo_response_blob(self):
        return self._manager_action(
            ("get_cryo_response_blob", (), {}), protocol=EL_PROTOCOL
        )

    def get_response_blob(self):
        """
        Get the extraction device's response blob

        :return: response blob. binary string representing time v measured output
        :rtype: str
        """
        result = self._extraction_action(("get_response_blob", (), {}))
        return result or b""

    def get_output_blob(self):
        """
        Get the extraction device's output blob

        :return: output blob: binary string representing time v percent output
        :rtype: str
        """

        result = self._extraction_action(("get_output_blob", (), {}))
        return result or b""

    def get_setpoint_blob(self):
        """
        Get the extraction device's setpoint blob

        :return: setpoint blob: binary string representing time v requested setpoint
        :rtype: str
        """

        result = self._extraction_action(("get_setpoint_blob", (), {}))
        return result or b""

    def output_achieved(self):
        """
        Return a formated string with the extraction "heating" results::

            Requested Output= 100.000
            Achieved Output= 99.012

        :return: Formatted string with results
        :rtype: str
        """
        request = self.extract
        ach = self._extraction_action(("get_achieved_output", (), {}))
        try:
            request = float(request)
        except (ValueError, TypeError):
            request = 0

        try:
            ach = float(ach)
        except (ValueError, TypeError):
            ach = 0

        return ach, request

    def get_active_pid_parameters(self):
        result = self._extraction_action(("get_active_pid_parameters", (), {}))
        return result or ""

    def get_command_register(self):
        cm = super(ExtractionPyScript, self).get_command_register()
        return list(command_register.commands.items()) + cm

    def set_default_context(self, **kw):
        """
        provide default values for all the properties exposed in the script
        """
        for attr in ("analysis_type", "extract_device"):
            if attr not in kw:
                kw[attr] = ""

        self.setup_context(
            position="",
            pattern="",
            extract_value=0,
            extract_units="",
            tray="",
            ramp_rate=0,
            ramp_duration=0,
            duration=0,
            delay_after=0,
            cleanup=0,
            pre_cleanup=0,
            post_cleanup=0,
            cryo_temperature=0,
            light_value=0,
            beam_diameter=None,
            load_identifier="default_load",
            run_identifier="default_runid",
            **kw
        )

    # ==========================================================================
    # commands
    # ==========================================================================
    @verbose_skip
    @command_register
    def store_manometer_pressure(self, idx=0):
        result = self._manager_action(
            ("get_manometer_pressure", (), {"idx": idx}), protocol=EL_PROTOCOL
        )
        self.extraction_context["manometer_pressure{}".format(idx)] = result
        return result

    @verbose_skip
    @command_register
    def get_manometer_pressure(self, idx=0):
        result = self._manager_action(
            ("get_manometer_pressure", (), {"idx": idx}), protocol=EL_PROTOCOL
        )
        return result

    @verbose_skip
    @command_register
    def get_pressure(self, controller, gauge):
        result = self._manager_action(
            ("get_pressure", (controller, gauge), {}), protocol=EL_PROTOCOL
        )
        return result

    @verbose_skip
    @command_register
    def start_cryo_recorder(self):
        result = self._manager_action(("start_cryo_recorder",), protocol=EL_PROTOCOL)
        return result

    @verbose_skip
    @command_register
    def stop_cryo_recorder(self):
        result = self._manager_action(("stop_cryo_recorder",), protocol=EL_PROTOCOL)
        return result

    @verbose_skip
    @command_register
    def set_cryo(self, value, device_name=None, block=False, delay=1):
        result = self._manager_action(
            (
                "set_cryo",
                (value,),
                {"block": block, "device_name": device_name, "delay": delay},
            ),
            protocol=EL_PROTOCOL,
        )

        self.debug("set cryo result={}".format(result))
        return result

    @verbose_skip
    @command_register
    def get_cryo_temp(self, value=1):
        result = self._manager_action(
            ("get_cryo_temp", (value,), {}), protocol=EL_PROTOCOL
        )
        return result

    @calculate_duration
    @command_register
    def begin_heating_interval(
        self,
        duration,
        min_rise_rate=None,
        check_time=60,
        check_delay=60,
        check_period=1,
        temperature=None,
        timeout=300,
        tol=10,
        name=None,
        calc_time=False,
    ):
        duration = float(duration)
        if calc_time:
            self._estimated_duration += duration

        if self._cancel:
            return

        def wait(dur, flag, n):
            if not min_rise_rate:
                self._sleep(dur)
            else:
                st = time.time()
                self._sleep(check_delay, "Heating check delay")

                t1 = time.time()
                r1 = self._extraction_action(("get_process_value",))

                self._sleep(check_time, "Checking rise rate")
                t2 = time.time()
                r2 = self._extraction_action(("get_process_value",))

                rr = (r2 - r1) / (t2 - t1)
                if rr < min_rise_rate:
                    self.warning(
                        "Failed to heat. Rise Rate={:0.1f}. Min Rise Rate={:0.1f}".format(
                            rr, min_rise_rate
                        )
                    )
                    self.cancel()
                    flag.set()
                else:
                    if temperature:
                        self._set_extraction_state(
                            "Waiting to reach temperature {}".format(temperature)
                        )
                        st = time.time()
                        while 1:
                            sti = time.time()
                            if sti - st < timeout:
                                self._set_extraction_state(
                                    "Failed to reach temperature {}".format(r2)
                                )
                                self.warning(
                                    "Failed to reach temperature {}".format(r2)
                                )
                                self.cancel()
                                break

                            r2 = self._extraction_action(("get_process_value",))
                            if r2:
                                if abs(r2 - temperature) < tol:
                                    self._set_extraction_state(
                                        "Reached Temperature {}".format(r2)
                                    )
                                    break
                            else:
                                self.warning("Failed to get response.")
                                self.cancel()
                                break
                            time.sleep(max(0, check_period - (time.time() - sti)))
                        self._sleep(dur, "Time at Temperature")

                    else:
                        rem = dur - (time.time - st)
                        self._sleep(
                            rem,
                        )

            if not self._cancel:
                self.console_info("{} finished".format(n))
                flag.set()

        t, f = None, None
        if name is None:
            name = "Interval {}".format(self._interval_stack.qsize() + 1)

        if not self.testing_syntax:
            f = Event()
            self.console_info(
                "BEGIN HEATING INTERVAL {} waiting for {}".format(name, duration)
            )
            t = Thread(name=name, target=wait, args=(duration, f, name))
            t.start()

        self._interval_stack.put((t, f, name))

    def _set_extraction_state(self, msg, color="red", flash=False):
        self._manager_action(
            ("set_extract_state", (msg,), {"color": color, "flash": flash})
        )

    @verbose_skip
    @command_register
    def set_response_recorder_period(self, p):
        self._extraction_action(("set_response_recorder_period", (p,), {}))

    @verbose_skip
    @command_register
    def start_response_recorder(self):
        self._extraction_action(("start_response_recorder",))

    @verbose_skip
    @command_register
    def stop_response_recorder(self):
        self._extraction_action(("stop_response_recorder",))

    @verbose_skip
    @command_register
    def check_reached_setpoint(self):
        self._extraction_action(("check_reached_setpoint",))

    @verbose_skip
    @command_register
    def wake(self):
        self._extraction_action("wake")
        self._manager_actions("wake")

    @verbose_skip
    @command_register
    def pause(self, delay=2):
        self._sleep(delay, paused=True)

    @verbose_skip
    @command_register
    def waitfor(
        self,
        func_or_tuple,
        start_message="",
        end_message="",
        check_period=1,
        timeout=0,
        func_kw=None,
    ):
        """

        tuple format: (device_name, function_name, comparison, ...)
        addition tuple elements are passed to function_name

        comparison ::

          x<10
          10<x<20

        callable can of form ``func() or func(ti) or func(ti, i)``
        where ``ti`` is the current relative time (relative to start of waitfor) and ``i`` is a counter

        :param func_or_tuple: wait for function to return True
        :type func_or_tuple: callable, tuple
        :param start_message: Message to display at start
        :type start_message: str
        :param end_message: Message to display at end
        :type end_message: str
        :param check_period: Delay between checks in seconds
        :type check_period: int, float
        :param timeout: Cancel waiting after ``timeout`` seconds
        :type timeout: int, float
        """
        include_time = False
        include_time_and_count = False
        if isinstance(func_or_tuple, tuple):
            func = self._make_waitfor_func(*func_or_tuple, func_kw=func_kw)
        else:
            func = func_or_tuple
            args = inspect.getfullargspec(func).args
            if len(args) == 1:
                include_time = True
            elif len(args) == 2:
                include_time_and_count = True

        if not func:
            self.debug("no waitfor function")
            self.cancel()

        self.console_info("waitfor started. {}".format(start_message))
        st = time.time()
        i = 0
        while 1:
            if self.is_canceled():
                self.console_info("waitfor canceled")
                return

            ct = time.time() - st
            if timeout and ct > timeout:
                self.warning("waitfor timed out after {}s".format(timeout))
                self.cancel()
                return

            if include_time:
                args = (ct,)
            elif include_time_and_count:
                args = (ct, i)
                i += 1
            else:
                args = tuple()

            if func(*args):
                self.console_info("waitfor ended. {}".format(end_message))
                break

            time.sleep(check_period)

    @verbose_skip
    @command_register
    def power_map(self, cx, cy, padding, bd, power):
        pass

    # @verbose_skip
    # @command_register
    # def degas(self, lumens=0, duration=0):
    #     self._extraction_action([('do_machine_vision_degas', (lumens, duration), {})])

    @verbose_skip
    @command_register
    def autofocus(self, set_zoom=True):
        self._extraction_action(("do_autofocus", (), {"set_zoom": set_zoom}))

    @verbose_skip
    @command_register
    def set_light(self, value=""):
        self._extraction_action(("set_light", (value,), {}))

    @verbose_skip
    @command_register
    def snapshot(self, name="", prefix="", view_snapshot=False, pic_format=".jpg"):
        """
        if name not specified use RID_Position e.g 12345-01A_3
        """
        if not name:
            pos = "_".join(self.position)
            name = "{}_{}".format(self.run_identifier, pos)

        name = "{}{}".format(prefix, name)
        snap = self._extraction_action(
            ("take_snapshot", (name, pic_format), {"view_snapshot": view_snapshot})
        )
        if snap:
            self.snapshots.append(snap)

    @command_register
    def grain_polygon(self):
        return GrainPolygonCTX(self)

    @command_register
    def lighting(self, value=75):
        return LightingCTX(self, value)

    @command_register
    def video_recording(self, name="video"):
        return RecordingCTX(self, name)

    @verbose_skip
    @command_register
    def start_video_recording(self, name="video"):
        self._extraction_action(("start_video_recording", (), {"name": name}))

    @verbose_skip
    @command_register
    def stop_video_recording(self, save_db=True):
        ps = self._extraction_action(("stop_video_recording",))
        if save_db:
            if ps:
                self.videos.append(ps)

    @verbose_skip
    @command_register
    def set_x(self, value, velocity=""):
        self._set_axis("x", value, velocity)

    @verbose_skip
    @command_register
    def set_y(self, value, velocity=""):
        self._set_axis("y", value, velocity)

    @verbose_skip
    @command_register
    def set_z(self, value, velocity=""):
        self._set_axis("z", value, velocity)

    @verbose_skip
    @command_register
    def set_xy(self, value, velocity=""):
        self._set_axis("xy", value, velocity)

    @verbose_skip
    @command_register
    def set_motor_lock(self, name="", value=""):
        if name and value is not "":
            l = "YES" if value else "NO"
            self.console_info("set motor lock to {}".format(name, l))
            self._extraction_action(("set_motor_lock", (name, value), {}))

    @verbose_skip
    @command_register
    def set_motor(self, name="", value=""):
        self.console_info('setting motor "{}" to {}'.format(name, value))
        if name is not "" and value is not "":
            if value is not None:
                self._extraction_action(("set_motor", (name, value), {}))

    @verbose_skip
    @command_register
    def get_value(self, name):
        try:
            print(name, self.get_context()[name])
            return self.get_context()[name]
        except KeyError:
            self.warning("no name {} in context".format(name))
            pass

    @verbose_skip
    @command_register
    def move_to_position(self, position="", autocenter=True, block=True):
        if position == "":
            position = self.position

        if position:
            position_ok = True
            if isinstance(position, (list, tuple)):
                position_ok = all(position)
        else:
            position_ok = False

        if position_ok:
            ed = self.extract_device
            self.console_info("{} move to position {}".format(ed, position))
            success = self._extraction_action(
                (
                    "move_to_position",
                    (position,),
                    {"autocenter": autocenter, "block": block},
                )
            )

            if not success:
                self.info("{} move to position failed".format(ed))
                self.cancel()
            else:
                self.console_info("move to position succeeded")
                return True
        else:
            self.console_info("move not required. position is None")
            return True

    @verbose_skip
    @command_register
    def dump_sample(self):
        success = self._extraction_action(("dump_sample", (), {"block": True}))

        if not success:
            self.info("{} dump sample failed".format(self.extract_device))
            self.cancel()
        else:
            self.console_info("dump sample succeeded")
            return True

    @verbose_skip
    @command_register
    def drop_sample(self, position=""):
        success = self._extraction_action(
            [("drop_sample", (position,), {"block": True})]
        )

        if not success:
            self.info("{} drop sample failed".format(self.extract_device))
            self.cancel()
        else:
            self.console_info("drop sample succeeded")
            return True

    @verbose_skip
    @command_register
    def execute_pattern(self, pattern="", block=True, duration=None):
        if pattern == "":
            pattern = self.pattern

        st = time.time()
        # set block=True to wait for pattern completion
        self._extraction_action(
            ("execute_pattern", (pattern,), {"block": block,
                                             "duration": duration,
                                             "position": self.position[0]})
        )

        return time.time() - st

    @verbose_skip
    @command_register
    def set_tray(self, tray=""):
        if tray == "":
            tray = self.tray

        self.console_info("set tray to {}".format(tray))
        result = self._extraction_action(("set_stage_map", (tray,), {}))
        return result

    @verbose_skip
    @command_register
    def load_pipette(self, identifier, timeout=300):
        """
        this is a non blocking command. it simply sends a command to apis to
        start one of its runscripts.

        it is the ExtractionPyScripts responsiblity to handle the waiting.
        use the waitfor command to wait for signals from apis.
        """
        from pychron.external_pipette.apis_manager import InvalidPipetteError

        if self.analysis_type == "blank":
            cmd = "load_blank_non_blocking"
        else:
            cmd = "load_pipette_non_blocking"
        try:
            # bug _manager_action only with except tuple of len 1 for args
            ret = self._extraction_action(
                (cmd, (identifier,), {"timeout": timeout}),
                name="externalpipette",
                protocol=IPipetteManager,
            )

            return ret
        except InvalidPipetteError as e:
            self.cancel(protocol=IPipetteManager)
            e = str(e)
            self.warning(e)
            return e

    @verbose_skip
    @command_register
    def extract_pipette(self, identifier="", timeout=300):
        """
        this is an atomic command. use the apis_controller config file to define
        the isolation procedures.
        """
        from pychron.external_pipette.apis_manager import InvalidPipetteError

        if identifier == "":
            identifier = self.extract_value

        cmd = "load_blank" if self.analysis_type == "blank" else "load_pipette"
        try:
            # bug _manager_action only with except tuple of len 1 for args
            result = self._extraction_action(
                (cmd, (identifier,), {"timeout": timeout, "script": self}),
                name="externalpipette",
                protocol=IPipetteManager,
            )

            return result
        except (TimeoutError, InvalidPipetteError) as e:
            self.cancel(protocol=IPipetteManager)
            e = str(e)
            self.warning(e)
            return e

    @verbose_skip
    @command_register
    def set_pid_parameters(self, v):
        self._extraction_action(("set_pid_parameters", (v,), {}))

    @verbose_skip
    @command_register
    def warmup(self, block=False):
        self._extraction_action(
            (
                "warmup",
                (),
                {
                    "block": block,
                },
            )
        )

    @verbose_skip
    @command_register
    def extract(self, power="", units="", block=None):
        if power == "":
            power = self.extract_value
        if units == "":
            units = self.extract_units

        ed = self.extract_device
        ed = ed.replace("_", " ")

        # get current position and add as an extraction position
        pos = self._extraction_action(("get_position", (), {}))
        self._extraction_positions.append(pos)

        msg = "{} ON! {}({})".format(ed, power, units)
        self._set_extraction_state(msg)
        self.console_info("extract sample to {} ({})".format(power, units))
        self._extraction_action(("extract", (power,), {"units": units, "block": block}))

    @verbose_skip
    @command_register
    def end_extract(self):
        self._set_extraction_state(False)
        self._extraction_action(("end_extract",))

    @verbose_skip
    @command_register
    def acquire_grain_polygon_blob(self):
        result = self._extraction_action(("acquire_grain_polygon",))
        if result:
            self._grain_polygons.append(result)

    @verbose_skip
    @command_register
    def start_grain_polygon(self):
        self._extraction_action(("start_measure_grain_polygon",))

    @verbose_skip
    @command_register
    def stop_grain_polygon(self):
        self._extraction_action(("stop_measure_grain_polygon",))

    @verbose_skip
    @command_register
    def fire_laser(self):
        self._extraction_action(("fire_laser",))

    @verbose_skip
    @command_register
    def ramp(self, start=0, setpoint=0, duration=0, rate=0, period=1):
        args = start, setpoint, duration, rate, period
        self.debug(
            "ramp parameters start={}, "
            "setpoint={}, duration={}, rate={}, period={}".format(*args)
        )

        def func(i, ramp_step):
            if self._cancel:
                self.debug("script canceled. exit ramp")
                return

            self.console_info("ramp step {}. setpoint={}".format(i, ramp_step))
            if not self._extraction_action(("set_laser_power", (ramp_step,), {})):
                self.debug("setting laser power during ramping failed")
                return

            return True

        st = time.time()
        rmp = Ramper()
        rmp.ramp(func, start, setpoint, duration, rate, period)
        return time.time() - st

    @verbose_skip
    @command_register
    def acquire(self, name=None, clear=False):
        if self.runner is None:
            self.debug("+++++++++++++++++++++++ Runner is None")
            return

        self.console_info("acquire {}".format(name))

        r = self.runner.get_resource(name)

        if not clear:
            if r.isSet():
                self.console_info("waiting for access")

                # if self.manager:
                #     msg = 'Waiting for Resource Access. "{}"'.format(name)
                #     self.manager.set_extract_state(msg, color='red')
                msg = 'Waiting for Resource Access. "{}"'.format(name)
                self._set_extraction_state(msg)
                while r.isSet():
                    if self._cancel:
                        break
                    self._sleep(1)

                    if not self.runner.reset_connection():
                        self.cancel()
                        break

        if not self._cancel:
            self._resource_flag = r
            self.runner.acquire(name)
            self.console_info("{} acquired".format(name))

        self._set_extraction_state(False)
        # if self.manager:
        #     self.manager.set_extract_state(False)

    @verbose_skip
    @command_register
    def wait(self, name=None, criterion=0):
        if self.runner is None:
            self.debug("+++++++++++++++++++++++ Runner is None")
            return

        self.console_info("waiting for {} = {}".format(name, criterion))
        r = self.runner.get_resource(name)

        cnt = 0
        resp = r.read()
        if resp is not None:
            while resp != criterion:
                time.sleep(1)

                # only verbose every 10s
                resp = r.read(verbose=cnt % 10 == 0)
                if resp is None:
                    continue

                cnt += 1
                if cnt > 100:
                    cnt = 0

        self.console_info("finished waiting")

    @verbose_skip
    @command_register
    def release(self, name=None):
        self.console_info("release {}".format(name))
        if self.runner is None:
            self.debug("+++++++++++++++++++++++ Runner is None")
            return

        if not self.runner.release(name):
            self.console_info("Could not release {}".format(name))

    @verbose_skip
    @command_register
    def set_resource(self, name=None, value=1):
        if self.runner is None:
            self.debug("+++++++++++++++++++++++ Runner is None")
            return

        r = self.runner.get_resource(name)
        if r is not None:
            r.set(value)
        else:
            self.console_info("Could not set {}".format(name))

    @verbose_skip
    @command_register
    def get_resource_value(self, name=None):
        if self.runner is None:
            self.debug("+++++++++++++++++++++++ Runner is None")
            return

        r = self.runner.get_resource(name)
        resp = None
        if r is not None:
            if hasattr(r, "get"):
                resp = r.get()
            else:
                resp = r.isSet()
        else:
            self.console_info("Could not get {}".format(name))

        self.debug("Get Resource Value {}={}".format(name, resp))
        return resp

    @verbose_skip
    @command_register
    def enable(self):
        ed = self.extract_device
        ed = ed.replace("_", " ")
        self._set_extraction_state("{} Enabled".format(ed), flash=False)
        # self.manager.set_extract_state('{} Enabled'.format(ed))

        return self._manager_action(
            ("enable_device", (), {}), protocol=ILaserManager, name=self.extract_device
        )

    @verbose_skip
    @command_register
    def disable(self):
        return self._disable()

    @verbose_skip
    @command_register
    def prepare(self):
        return self._extraction_action(("prepare", (), {}))

    @verbose_skip
    @command_register
    def set_intensity_scalar(self, v):
        return self._automated_run_call("py_set_intensity_scalar", v)

    @verbose_skip
    @command_register
    def get_device(self, name):
        return self._get_device(name)

    # ==========================================================================
    # properties
    # ==========================================================================
    @property
    def duration(self):
        return self._get_property(DURATION)

    @property
    def cleanup(self):
        return self._get_property(CLEANUP)

    @property
    def pre_cleanup(self):
        return self._get_property(PRECLEANUP)

    @property
    def post_cleanup(self):
        return self._get_property(POSTCLEANUP)

    @property
    def cryo_temperature(self):
        return self._get_property(CRYO_TEMP)

    @property
    def pattern(self):
        return self._get_property(PATTERN)

    @property
    def analysis_type(self):
        at = self._get_property("analysis_type")
        self.debug(
            "getting analysis type for {}. "
            "analysis_type={}".format(self.run_identifier, at)
        )
        return at

    @property
    def extract_device(self):
        return self._get_property("extract_device")

    @property
    def tray(self):
        return self._get_property("tray")
        # return self.get_context()['tray']

    @property
    def position(self):
        """
        if position is 0 return None
        """
        # pos = self.get_context()['position']
        pos = self._get_property("position")
        if pos:
            return pos

    @property
    def extract_value(self):
        return self._get_property("extract_value")
        # return self.get_context()['extract_value']

    @property
    def extract_units(self):
        return self._get_property("extract_units")
        # return self.get_context()['extract_units']

    @property
    def beam_diameter(self):
        return self._get_property("beam_diameter")
        # return self.get_context()['beam_diameter']

    @property
    def run_identifier(self):
        return self._get_property("run_identifier")

    @property
    def load_identifier(self):
        return self._get_property("load_identifier")

    @property
    def light_value(self):
        return self._get_property("light_value")

    # ===============================================================================
    # private
    # ===============================================================================
    def _failed_actuation_hook(self):
        self._automated_run_call("set_end_after")

    def _check_responding(self, rr, st):
        self._extraction_action(("check_responding", (rr, st), {}))

    def _abort_hook(self):
        self.disable()

    # def _cancel_hook(self):
    #     self.disable()

    def _get_device(self, name):
        app = self._get_application()
        if app is not None:
            return app.get_service_by_name(ICoreDevice, name)
        else:
            self.warning("_get_device - No application")

    def _make_waitfor_func(self, name, funcname, comp, func_kw=None):
        if func_kw is None:
            func_kw = {}

        dev = self._get_device(name)
        if dev:
            devfunc = getattr(dev, funcname)
            m = COMPRE.findall(comp)
            if m:
                k = m[0]

                def func(*a):
                    print("devfunc", devfunc(**func_kw))
                    print("eval", eval(comp, {k: devfunc(**func_kw)}))
                    return eval(comp, {k: devfunc(**func_kw)})

                return func
            else:
                self.warning("invalid comparison. valid e.g.=x<10 comp={}".format(comp))
        else:
            self.warning('no device available named "{}"'.format(name))

    def _extraction_action(self, *args, **kw):
        if "name" not in kw or kw["name"] is None:
            kw["name"] = self.extract_device
        if "protocol" not in kw or kw["protocol"] is None:
            kw["protocols"] = ILaserManager, IFurnaceManager

        if kw["name"] in (
            "Extract Device",
            "ExtractDevice",
            "extract device",
            "extractdevice",
            NULL_STR,
            LINE_STR,
        ):
            self.debug("no extraction action")
            return

        return self._manager_action(*args, **kw)

    def _extraction_actions(self, *args, **kw):
        if "name" not in kw or kw["name"] is None:
            kw["name"] = self.extract_device
        if "protocol" not in kw or kw["protocol"] is None:
            kw["protocols"] = ILaserManager, IFurnaceManager

        if kw["name"] in (
            "Extract Device",
            "ExtractDevice",
            "extract device",
            "extractdevice",
            NULL_STR,
            LINE_STR,
        ):
            self.debug("no extraction action")
            return

        return self._manager_actions(*args, **kw)

    def _disable(self, protocol=None):
        self.debug("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% disable")
        self._set_extraction_state(False)
        # if self.manager:
        #     self.manager.set_extract_state(False)

        return self._extraction_action(("disable_device", (), {}), protocol=protocol)

    def _set_axis(self, name, value, velocity):
        kw = dict(block=True)
        if velocity:
            kw["velocity"] = value

        success = self._extraction_action(("set_{}".format(name), (value,), kw))
        if not success:
            self.console_info("{} move to position failed".format(self.extract_device))
        else:
            self.console_info("move to position suceeded")
        return True

    def _cancel_hook(self, **kw):
        if self._resource_flag:
            self._resource_flag.clear()

        # disable the extract device
        self._disable(**kw)

        # stop patterning
        self._stop_pattern(**kw)
        self.stop_grain_polygon()

    def _stop_pattern(self, protocol=None):
        self._extraction_action(("stop_pattern", (), {}), protocol=protocol)

    def _automated_run_call(self, func, *args, **kw):
        if self.automated_run is None:
            return

        if isinstance(func, str):
            func = getattr(self.automated_run, func)

        return func(*args, **kw)


# ============= EOF ====================================
