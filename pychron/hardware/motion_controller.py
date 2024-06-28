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

# ============= enthought library imports =======================
from traits.api import Property, Dict, Float, Any, Instance, Bool
from traitsui.api import View, VGroup, Item, RangeEditor

# ============= standard library imports ========================
import os
import time

# ============= local library imports  ==========================
from pychron.core.codetools.inspection import caller
from pychron.core.helpers.strtools import csv_to_floats
from pychron.core.helpers.timer import Timer
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.motion.motion_profiler import MotionProfiler


# from pychron.hardware.utilities import limit_frequency
class PositionError(BaseException):
    def __init__(self, x, y, z=None):
        self._y = y
        self._x = x

    def __str__(self):
        return "PositionError. x={}, y={}".format(self._x, self._y)


class TargetPositionError(BaseException):
    def __init__(self, x, y, tx, ty):
        self._tx = tx
        self._ty = ty
        self._y = y
        self._x = x

    def __str__(self):
        dx = self._x - self._tx
        dy = self._y - self._ty
        return (
            "PositionError. Dev:{},{} Current: x={}, y={}, Target: x={}, y={}".format(
                dx, dy, self._x, self._y, self._tx, self._ty
            )
        )


class ZeroDisplacementException(BaseException):
    pass


class MotionController(CoreDevice):
    """ """

    axes = Dict
    xaxes_max = Property
    xaxes_min = Property
    yaxes_max = Property
    yaxes_min = Property
    zaxes_max = Property
    zaxes_min = Property

    group_parameters = None
    timer = None
    parent = Any

    x = Property(trait=Float(enter_set=True, auto_set=False), depends_on="_x_position")
    _x_position = Float
    y = Property(trait=Float(enter_set=True, auto_set=False), depends_on="_y_position")
    _y_position = Float

    z = Property(trait=Float(enter_set=True, auto_set=False), depends_on="_z_position")

    _z_position = Float
    z_progress = Float
    motion_profiler = Instance(MotionProfiler)

    groupobj = None
    _not_moving_count = 0
    _homing = False
    _stopped = True
    nonstoppable = Bool(False)

    def xy_swapped(self):
        return False

    def update_position(self):
        pass

    def update_axes(self):
        for a in self.axes:
            pos = self.get_current_position(a)
            if pos is not None:
                setattr(self, "_{}_position".format(a), pos)
                #            time.sleep(0.075)
        self.z_progress = self._z_position

        #        def _update():
        #        print self._x_position, self._y_position
        self.parent.canvas.set_stage_position(self._x_position, self._y_position)

    # @caller
    def timer_factory(self, func=None, period=150):
        """

        reuse timer if func is the same

        """
        self._stopped = False
        timer = self.timer
        if func is None:
            func = self._inprogress_update

        if timer is None:
            self._not_moving_count = 0
            timer = Timer(period, func, delay=250)
        elif timer.func == func:
            if timer.isActive():
                self.debug("reusing old timer")
            else:
                self._not_moving_count = 0
                timer = Timer(period, func, delay=250)
        else:
            timer.stop()
            self._not_moving_count = 0
            # time.sleep(period / 1000.)
            timer = Timer(period, func, delay=period)

        timer.set_interval(period)
        return timer

    @caller
    def set_z(self, v, **kw):
        if v != self._z_position:
            self.single_axis_move("z", v, **kw)
            #        setattr(self, '_{}_position'.format('z'), v)
            self._z_position = v
            self.axes["z"].position = v

    def in_motion(self):
        if self.timer:
            return self.timer.isActive()

    def moving(self, *args, **kw):
        return self._moving(*args, **kw)

    def block(self, *args, **kw):
        self._block(*args, **kw)

    def axes_factory(self, config=None):
        if config is None:
            config = self.get_configuration(self.config_path)

        mapping = self.config_get(config, "General", "mapping")
        if mapping is None:
            mapping = "x,y,z"
        mapping = mapping.split(",")

        lp = self.config_get(config, "General", "loadposition")
        if lp is not None:
            loadposition = csv_to_floats(lp)
        else:
            loadposition = [0, 0, 0]

        config_path = self.configuration_dir_path
        for i, a in enumerate(mapping):
            self.info("loading axis {},{}".format(i, a))
            limits = csv_to_floats(config.get("Axes Limits", a))

            na = self._axis_factory(
                config_path,
                name=a,
                id=i + 1,
                negative_limit=limits[0],
                positive_limit=limits[1],
                loadposition=loadposition[i],
                min_velocity=self.motion_profiler.min_velocity,
                max_velocity=self.motion_profiler.max_velocity,
            )

            self.axes[a] = na
            self.debug("asdfasdfsafsadf {}".format(self.axes))

    def get_current_xy(self):
        x = self.get_current_position("x")
        y = self.get_current_position("y")
        if x is None or y is None:
            return
        return x, y

    # ===============================================================================
    # define in subclass
    # ===============================================================================

    def save_axes_parameters(self):
        pass

    def get_xyz(self):
        return 0, 0, 0

    def get_current_positions(self, keys):
        return 0 * len(keys)

    def get_current_position(self, *args, **kw):
        return 0

    def execute_command_buffer(self, *args, **kw):
        pass

    #    def enqueue_move(self, *args, **kw):
    #        pass

    def set_smooth_transitions(self, *args, **kw):
        pass

    def set_program_mode(self, *args, **kw):
        pass

    def linear_move(self, *args, **kw):
        pass

    def set_home_position(self, *args, **kw):
        pass

    def single_axis_move(self, *args, **kw):
        pass

    def define_home(self):
        pass

    def home(self, *args, **kw):
        pass

    def set_single_axis_motion_parameters(self, *args, **kw):
        pass

    def stop(self, *args, **kw):
        pass

    # ===============================================================================
    # private
    # ===============================================================================
    def _set_axis(self, name, v, **kw):
        if v is None:
            return

        c = getattr(self, "_{}_position".format(name))

        disp = abs(c - v)
        if c == v or disp < 0.001:
            return

        self.debug("set axis {} to {}. current pos={}".format(name, v, c))
        self.single_axis_move(name, v, update=disp > 4, **kw)

        self.axes[name].position = v

        if disp <= 4:
            self.parent.canvas.clear_desired_position()

    def _moving(self, *args, **kw):
        pass

    def _z_inprogress_update(self):
        """ """

        self._check_moving(axis="z", verbose=True)

        z = self.get_current_position("z")
        self.z_progress = z

    def _check_moving(self, axis=None, verbose=True):
        m = self._moving(axis=axis, verbose=verbose)
        if verbose:
            self.debug("is moving={}".format(m))

        stopped = False
        if not m:
            self._not_moving_count += 1
        else:
            self._not_moving_count = 0

        if self._not_moving_count > 1:
            if verbose:
                self.debug("not moving cnt={}".format(self._not_moving_count))
            self._not_moving_count = 0
            if self.timer:
                if verbose:
                    self.debug("stop timer")
                self.timer.Stop()
            stopped = True
        return stopped

    def _inprogress_update(self):
        """ """
        stopped = self._check_moving()
        if stopped:
            self.parent.canvas.clear_desired_position()
            self.update_axes()
        else:
            xy = self.get_current_xy()
            if xy:
                self._validate_xy(*xy)
                self.parent.canvas.set_stage_position(*xy)

    def _validate_xy(self, x, y):
        if self._homing:
            return

        vx = self.xaxes_min - 2 <= x <= self.xaxes_max + 2
        vy = self.yaxes_min - 2 <= y <= self.yaxes_max + 2
        # print x,y,vx,vy, self.xaxes_min, self.xaxes_max
        if not (vx and vy):
            self.timer.stop()
            self.stop()
            raise PositionError(x, y)

    def _sign_correct(self, val, key, ratio=True):
        """ """
        if val is not None:
            axis = self.axes[key]
            r = 1
            if ratio:
                r = axis.drive_ratio

            return val * axis.sign * r

    def _block(self, axis=None, event=None):
        """ """
        self.debug("block")
        if event is not None:
            event.clear()

        timer = self.timer

        if timer is not None:
            self.debug("using existing timer")
            period = 0.15

            def func():
                return timer.isActive()

        else:
            self.debug("check moving={}".format(axis))
            period = 0.15

            def func():
                return self._moving(axis=axis, verbose=True)

        cnt = 0
        threshold = 0 if timer else 1
        while 1:
            st = time.time()
            a = func()
            et = time.time() - st

            if not a:
                cnt += 1
                if cnt > threshold:
                    break
            else:
                cnt = 0

            s = max(0, period - et)
            if s:
                time.sleep(s)

        self.debug("block finished")

        if event is not None:
            event.set()

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_x(self):
        return self._x_position

    def _get_y(self):
        return self._y_position

    def _get_z(self):
        return self._z_position

    def _set_x(self, v):
        self._set_axis("x", v)

    def _set_y(self, v):
        self._set_axis("y", v)

    def _set_z(self, v):
        if v is not None:
            self.set_z(v)

    def _validate_x(self, v):
        return self._validate(v, "x", self._x_position)

    def _validate_y(self, v):
        return self._validate(v, "y", self._y_position)

    def _validate_z(self, v):
        return self._validate(v, "z", self._z_position)

    def _validate(self, v, key, cur):
        """ """
        try:
            ax = self.axes[key]
        except KeyError:
            return

        mi = ax.negative_limit
        ma = ax.positive_limit
        self.debug("validate axis={} value={} current={}".format(key, v, cur))
        try:
            v = float(v)
            if not mi <= v <= ma:
                self.debug("value not between {}, {}".format(mi, ma))
                v = None
                #
                # if v is not None:
                #     if abs(v - cur) <= 0.001:
                #         v = None
        except ValueError:
            v = None

        return v

    def _get_xaxes_max(self):
        return self._get_positive_limit("x")

    def _get_xaxes_min(self):
        return self._get_negative_limit("x")

    def _get_yaxes_max(self):
        return self._get_positive_limit("y")

    def _get_yaxes_min(self):
        return self._get_negative_limit("y")

    def _get_zaxes_max(self):
        return self._get_positive_limit("z")

    def _get_zaxes_min(self):
        return self._get_negative_limit("z")

    def _get_positive_limit(self, key):
        return self.axes[key].positive_limit if key in self.axes else 0

    def _get_negative_limit(self, key):
        return self.axes[key].negative_limit if key in self.axes else 0

    # ===============================================================================
    # view
    # ===============================================================================
    def traits_view(self):
        grp = self.get_control_group()
        grp.label = ""
        grp.show_border = False
        return View(grp)

    def get_control_group(self):
        g = VGroup(show_border=True, label="Axes")

        keys = list(self.axes.keys())
        keys.sort()
        for k in keys:
            editor = RangeEditor(
                low_name="{}axes_min".format(k),
                high_name="{}axes_max".format(k),
                mode="slider",
                format="%0.3f",
            )

            g.content.append(Item(k, editor=editor))
            if k == "z":
                g.content.append(
                    Item(
                        "z_progress", show_label=False, editor=editor, enabled_when="0"
                    )
                )
        return g

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _motion_profiler_default(self):
        mp = MotionProfiler()

        if self.configuration_dir_path:
            p = os.path.join(self.configuration_dir_path, "motion_profiler.cfg")
            mp.load(p)
        return mp


# ============= EOF ====================================
