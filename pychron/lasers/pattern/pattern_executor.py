# ===============================================================================
# Copyright 2012 Jake Ross
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

import os
import time
from io import StringIO
from threading import Event

from numpy import polyfit, array, average, uint8, zeros_like
from traits.api import Any, Bool

from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.thread import Thread, sleep
from pychron.envisage.view_util import open_view
from pychron.hardware.motion_controller import PositionError, TargetPositionError
from pychron.lasers.pattern.patternable import Patternable
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR


class PatternExecutor(Patternable):
    """
    a pattern is only good for one execution.
    self.pattern needs to be reset after stop or finish using load_pattern(name_or_pickle)
    """

    controller = Any
    laser_manager = Any
    show_patterning = Bool(False)
    _alive = Bool(False)

    def __init__(self, *args, **kw):
        super(PatternExecutor, self).__init__(*args, **kw)
        self._next_point = None
        self.pattern = None
        self._xy_thread = None
        self._power_thread = None
        self._z_thread = None

    def start(self, show=False):
        self._alive = True

        if show:
            self.show_pattern()

        if self.pattern:
            self.pattern.clear_graph()

    def finish(self):
        self._alive = False
        self.close_pattern()
        self.pattern = None

    def set_stage_values(self, sm):
        if self.pattern:
            self.pattern.set_stage_values(sm)

    def set_current_position(self, x, y, z):
        if self.isPatterning():
            graph = self.pattern.graph
            graph.set_data([x], series=1, axis=0)
            graph.set_data([y], series=1, axis=1)

            graph.add_datum((x, y), series=2)

            graph.redraw()

    def load_pattern(self, name_or_pickle):
        """
        look for name_or_pickle in local pattern dir

        if not found try interpreting name_or_pickle is a pickled name_or_pickle

        """
        if name_or_pickle is None:
            path = self.open_file_dialog()
            if path is None:
                return
        else:
            path = self.is_local_pattern(name_or_pickle)

        if path:
            wfile = open(path, "rb")
        else:
            # convert name_or_pickle into a file like obj
            wfile = StringIO(name_or_pickle)

        # self._load_pattern sets self.pattern
        pattern = self._load_pattern(wfile, path)

        self.on_trait_change(self.stop, "canceled")
        return pattern

    def is_local_pattern(self, name):
        def test_name(ni):
            path = os.path.join(paths.pattern_dir, ni)
            if os.path.isfile(path):
                return path

        for ni in (name, name + ".lp"):
            p = test_name(ni)
            if p:
                return p

    def stop(self):
        self._alive = False
        if self.controller:
            self.info("User requested stop")
            self.controller.stop()

        if self.pattern is not None:
            if self.controller:
                self.controller.linear_move(
                    self.pattern.cx, self.pattern.cy, source="pattern stop"
                )
            # self.pattern.close_ui()
            self.info("Pattern {} stopped".format(self.pattern_name))

            # prevent future stops (AbortJogs from massspec) from executing
            self.pattern = None

    def isPatterning(self):
        return self._alive

    def close_pattern(self):
        pass

    def show_pattern(self):
        self.pattern.window_x = 50
        self.pattern.window_y = 50
        open_view(self.pattern, view="graph_view")

    def execute(self, block=False, duration=None, thread_safe=True):
        """
        if block is true wait for patterning to finish
        before returning
        """
        if not self.pattern:
            return

        self.start(show=self.show_patterning)
        evt = None
        # if current_thread().name != 'MainThread':
        if thread_safe:
            evt = Event()
            invoke_in_main_thread(self._pre_execute, evt)
            while not evt.is_set():
                time.sleep(0.05)
        else:
            self._pre_execute(evt)

        self.debug("execute xy pattern")

        xyp = self.pattern.xy_pattern_enabled
        if duration:
            self.pattern.external_duration = float(duration)

        if xyp:
            self._xy_thread = Thread(target=self._execute_xy_pattern)
            self._xy_thread.start()

        pp = self.pattern.power_pattern
        if pp:
            self.debug("execute power pattern")
            self._power_thread = Thread(target=self._execute_power_pattern)
            self._power_thread.start()

        zp = self.pattern.z_pattern

        if zp:
            self.debug("execute z pattern")
            self._z_thread = Thread(target=self._execute_z_pattern)
            self._z_thread.start()

        if block:
            if self._xy_thread:
                self._xy_thread.join()
            if self._z_thread:
                self._z_thread.join()
            if self._power_thread:
                self._power_thread.join()

            self.finish()

    def _pre_execute(self, evt):
        self.debug("pre execute")
        pattern = self.pattern

        kind = pattern.kind
        if kind in ("SeekPattern", "DragonFlyPeakPattern"):
            self._info = open_view(pattern, view="execution_graph_view")

        if evt is not None:
            evt.set()
        self.debug("pre execute finished")

    def _execute_power_pattern(self):
        pat = self.pattern
        self.info("starting power pattern {}".format(pat.name))

        def func(v):
            self.laser_manager.set_laser_power(v)

        self._execute_(
            func, pat.power_values(), pat.power_sample, "power pattern setpoint={value}"
        )

    def _execute_z_pattern(self):
        pat = self.pattern
        self.info("starting power pattern {}".format(pat.name))

        def func(v):
            self.controller.set_z(v)

        self._execute_(func, pat.z_values(), pat.z_sample, "z pattern z={value}")

    def _execute_(self, func, vs, period, msg):
        for v in vs:
            st = time.time()
            self.debug(msg.format(value=v))
            func(v)

            et = st - time.time()
            p = period - et
            time.sleep(p)

    def _execute_xy_pattern(self):
        pat = self.pattern
        self.info("starting pattern {}".format(pat.name))
        st = time.time()
        self.controller.update_position()
        time.sleep(1)
        pat.cx, pat.cy = self.controller.x, self.controller.y
        try:
            for ni in range(pat.niterations):
                if not self.isPatterning():
                    break

                self.info("doing pattern iteration {}".format(ni))
                self._execute_iteration(ni)

            self.controller.nonstoppable = True
            self.controller.linear_move(
                pat.cx, pat.cy, block=True, source="execute_xy_pattern"
            )
            self.controller.nonstoppable = False

            if pat.disable_at_end:
                self.laser_manager.disable_device()

            self.finish()
            self.info(
                "finished pattern: transit time={:0.1f}s".format(time.time() - st)
            )

        except (TargetPositionError, PositionError) as e:
            self.finish()
            self.controller.stop()
            self.laser_manager.emergency_shutoff(str(e))

    def _execute_iteration(self, iteration):
        controller = self.controller
        pattern = self.pattern
        if controller is not None:

            kind = pattern.kind
            if kind == "ArcPattern":
                self._execute_arc(controller, pattern)
            elif kind == "CircularContourPattern":
                self._execute_contour(controller, pattern)
            elif kind in ("SeekPattern", "DragonFlyPeakPattern"):
                self._execute_seek(controller, pattern)
            else:
                self._execute_points(controller, pattern, iteration, multipoint=False)

    def _execute_points(self, controller, pattern, iteration, multipoint=False):
        pts = pattern.points_factory()
        if multipoint:
            controller.multiple_point_move(pts, velocity=pattern.velocity)
        else:
            for i, (x, y) in enumerate(pts):
                self.debug("Pattern Point. {},{}".format(iteration, i))
                if not self.isPatterning():
                    break

                # skip first point after first iteration
                if iteration and not i:
                    self.debug("skipping first point")
                    continue

                self.debug("Pattern Point. {},{}: {},{}".format(iteration, i, x, y))
                controller.linear_move(x, y, block=True, velocity=pattern.velocity)

    def _execute_contour(self, controller, pattern):
        for ni in range(pattern.nsteps):
            if not self.isPatterning():
                break

            r = pattern.radius * (1 + ni * pattern.percent_change)
            self.info("doing circular contour {} {}".format(ni + 1, r))
            controller.single_axis_move("x", pattern.cx + r, block=True)
            controller.arc_move(pattern.cx, pattern.cy, 360, block=True)
            time.sleep(0.1)

    def _execute_arc(self, controller, pattern):
        controller.single_axis_move("x", pattern.radius, block=True)
        controller.arc_move(pattern.cx, pattern.cy, pattern.degrees, block=True)

    def _execute_seek(self, controller, pattern):

        duration = pattern.duration
        total_duration = pattern.total_duration

        lm = self.laser_manager
        sm = lm.stage_manager
        ld = sm.lumen_detector

        ld.mask_kind = pattern.mask_kind
        ld.custom_mask = pattern.custom_mask_radius

        osdp = sm.canvas.show_desired_position
        sm.canvas.show_desired_position = False

        st = time.time()
        self.debug("Pre seek delay {}".format(pattern.pre_seek_delay))
        time.sleep(pattern.pre_seek_delay)

        self.debug("starting seek")
        self.debug("total duration {}".format(total_duration))
        self.debug("dwell duration {}".format(duration))

        if pattern.kind == "DragonFlyPeakPattern":
            try:
                self._dragonfly_peak(st, pattern, lm, controller)
            except BaseException as e:
                self.critical("Dragonfly exception. {}".format(e))
                self.debug_exception()
        else:
            self._hill_climber(st, controller, pattern)

        sm.canvas.show_desired_position = osdp

        from pyface.gui import GUI

        GUI.invoke_later(self._info.dispose)

    def _dragonfly_peak(self, st, pattern, lm, controller):
        from skimage.color import gray2rgb
        from skimage.draw import circle

        # imgplot, imgplot2, imgplot3 = pattern.setup_execution_graph()
        # imgplot, imgplot2 = pattern.setup_execution_graph()
        imgplot, imgplot2 = pattern.setup_execution_graph(nplots=2)
        cx, cy = pattern.cx, pattern.cy

        sm = lm.stage_manager

        linear_move = controller.linear_move
        in_motion = controller.in_motion
        find_lum_peak = sm.find_lum_peak
        pxpermm = sm.pxpermm

        set_data = imgplot.data.set_data
        set_data2 = imgplot2.data.set_data
        # set_data3 = imgplot3.data.set_data

        duration = pattern.duration
        sat_threshold = pattern.saturation_threshold
        total_duration = pattern.total_duration
        min_distance = pattern.min_distance
        aggressiveness = pattern.aggressiveness
        update_period = pattern.update_period / 1000.0
        move_threshold = pattern.move_threshold
        blur = pattern.blur
        px, py = cx, cy
        ncx, ncy = cx, cy

        point_gen = None
        cnt = 0
        # peak = None
        oimg = sm.get_preprocessed_src()
        pos_img = zeros_like(oimg, dtype="int16")
        per_img = zeros_like(oimg, dtype="int16")

        img_h, img_w = pos_img.shape
        perimeter_circle = circle(
            img_h / 2, img_w / 2, pattern.perimeter_radius * pxpermm
        )

        color = 2**15 - 1
        per_img[perimeter_circle] = 50
        set_data("imagedata", gray2rgb(per_img.astype(uint8)))

        while time.time() - st < total_duration:
            if not self._alive:
                break

            sats = []
            pts = []
            ist = time.time()
            npt = None
            self.debug("starting iteration={}, in_motion={}".format(cnt, in_motion()))
            while time.time() - ist < duration or in_motion():
                args = find_lum_peak(min_distance, blur)

                if args is None:
                    sleep(update_period / 5)
                    continue

                pt, peakcol, peakrow, peak_img, sat, src = args

                sats.append(sat)
                src = gray2rgb(src).astype(uint8)
                if pt:
                    pts.append(pt)
                    c = circle(peakrow, peakcol, 2)
                    # img[c] = (255, 0, 0)
                    src[c] = (255, 0, 0)

                set_data2("imagedata", src)

                sleep(update_period)

            self.debug("iteration {} finished, npts={}".format(cnt, len(pts)))

            pattern.position_str = NULL_STR

            if pts:
                w = array(sats)
                avg_sat_score = w.mean()
                self.debug(
                    "Average Saturation: {} threshold={}".format(
                        avg_sat_score, sat_threshold
                    )
                )
                pattern.average_saturation = avg_sat_score
                if avg_sat_score < sat_threshold:
                    # pts = array(pts)
                    x, y, w = array(pts).T
                    ws = w.sum()
                    nx = (x * w).sum() / ws
                    ny = (y * w).sum() / ws
                    self.debug("New point {},{}".format(nx, ny))
                    npt = nx, ny, 1
                else:
                    continue

            if npt is None:
                if not point_gen:
                    point_gen = pattern.point_generator()
                # wait = False
                x, y = next(point_gen)
                px, py = ncx + x, ncy + y
                self.debug("generating new point={},{} ---- {},{}".format(x, y, px, py))

            else:

                point_gen = None

                # # wait = True
                # if npt is None:
                #     block = total_duration - (time.time() - st) < duration
                #     linear_move(cx, cy, source='recenter_dragonfly{}'.format(cnt), block=block,
                #                 velocity=pattern.velocity,
                #                 use_calibration=False)
                #     pattern.position_str = 'Return to Center'
                #     px, py = cx, cy
                #     continue

                try:
                    scalar = npt[2]
                except IndexError:
                    scalar = 1

                ascalar = scalar * aggressiveness
                dx = npt[0] / pxpermm * ascalar
                dy = npt[1] / pxpermm * ascalar
                if abs(dx) < move_threshold or abs(dy) < move_threshold:
                    self.debug(
                        "Deviation too small dx={},dy={}".format(dx, dy, move_threshold)
                    )
                    pattern.position_str = "Deviation too small"
                    continue

                px += dx
                py -= dy
                self.debug(
                    "i: {}. point={},{}. "
                    "Intensitiy Scalar={}, Modified Scalar={}".format(
                        cnt, px, py, scalar, ascalar
                    )
                )

                ncx, ncy = px, py

            if not pattern.validate(px, py):
                self.debug("invalid position. {},{}".format(px, py))

                curx = px - dx
                cury = py + dy

                vx = curx - cx
                vy = cury - cy

                px = vx * aggressiveness + cx
                py = vy * aggressiveness + cy

                self.debug("reduced vector magnitude. new pos={},{}".format(px, py))

                # for safety validate this new position
                # if above calculation is correct the new position should always be valid
                if not pattern.validate(px, py):
                    self.debug(
                        "vector calculations incorrect. moving to center position"
                    )
                    px, py = cx, cy

                ncx, ncy = px, py

            pattern.position_str = "{:0.5f},{:0.5f}".format(px, py)

            # if there is less than 1 duration left then block is true
            block = total_duration - (time.time() - st) < duration
            self.debug("blocking ={}".format(block))

            try:
                linear_move(
                    px,
                    py,
                    source="dragonfly{}".format(cnt),
                    block=block,
                    velocity=pattern.velocity,
                    use_calibration=False,
                )
            except TargetPositionError as e:
                self.debug("Target position error: {}".format(e))

            ay, ax = py - cy, px - cx
            # self.debug('position mm ax={},ay={}'.format(ax, ay))
            ay, ax = int(-ay * pxpermm) + img_h / 2, int(ax * pxpermm) + img_w / 2
            # self.debug('position pixel ax={},ay={}'.format(ax, ay))

            pos_img -= 5
            pos_img = pos_img.clip(0, color)

            c = circle(ay, ax, 2)
            pos_img[c] = color - 60
            nimg = (pos_img + per_img).astype(uint8)

            set_data("imagedata", gray2rgb(nimg))

            cnt += 1

        self.debug("dragonfly complete")
        controller.block()

    def _hill_climber(self, st, controller, pattern):
        g = pattern.execution_graph
        imgplot, cp = pattern.setup_execution_graph()

        cx, cy = pattern.cx, pattern.cy

        sm = self.laser_manager.stage_manager
        linear_move = controller.linear_move
        get_scores = sm.get_scores
        moving = sm.moving
        update_axes = sm.update_axes
        set_data = imgplot.data.set_data

        sat_threshold = pattern.saturation_threshold
        total_duration = pattern.total_duration
        duration = pattern.duration
        pattern.perimeter_radius *= sm.pxpermm

        avg_sat_score = -1
        # current_x, current_y =None, None
        for i, pt in enumerate(pattern.point_generator()):
            update_plot = True

            x, y = pt.x, pt.y
            ax, ay = cx + x, cy + y
            if not self._alive:
                break

            if time.time() - st > total_duration:
                break

            # use_update_point = False
            if avg_sat_score < sat_threshold:
                # use_update_point = False
                # current_x, current_y = x, y
                linear_move(
                    ax,
                    ay,
                    block=False,
                    velocity=pattern.velocity,
                    use_calibration=False,
                    update=False,
                    immediate=True,
                )
            else:
                self.debug("Saturation target reached. not moving")
                update_plot = False

            density_scores = []
            ts = []
            saturation_scores = []
            positions = []

            def measure_scores(update=False):
                if update:
                    update_axes()

                positions.append((controller.x, controller.y))
                score_density, score_saturation, img = get_scores()

                density_scores.append(score_density)
                saturation_scores.append(score_saturation)

                set_data("imagedata", img)
                ts.append(time.time() - st)
                time.sleep(0.1)

            while moving(force_query=True):
                measure_scores(update=True)

            mt = time.time()
            while time.time() - mt < duration:
                measure_scores()

            if density_scores:
                n = len(density_scores)

                density_scores = array(density_scores)
                saturation_scores = array(saturation_scores)

                weights = [
                    1 / (max(0.0001, ((xi - ax) ** 2 + (yi - ay) ** 2)) ** 0.5)
                    for xi, yi in positions
                ]

                avg_score = average(density_scores, weights=weights)
                avg_sat_score = average(saturation_scores, weights=weights)
                score = avg_score

                m, b = polyfit(ts, density_scores, 1)
                if m > 0:
                    score *= 1 + m

                pattern.set_point(score, pt)

                self.debug("i:{} XY:({:0.5f},{:0.5f})".format(i, x, y))
                self.debug(
                    "Density. AVG:{:0.3f} N:{} Slope:{:0.3f}".format(avg_score, n, m)
                )
                self.debug("Modified Density Score: {:0.3f}".format(score))
                self.debug("Saturation. AVG:{:0.3f}".format(avg_sat_score))
                if update_plot:
                    cp.add_point((x, y))
                    g.add_datum((x, y), plotid=0)

                t = time.time() - st
                g.add_datum((t, avg_score), plotid=1)

                # g.add_bulk_data(ts, density_scores, plotid=1, series=1)

                g.add_datum(
                    (t, score),
                    ypadding="0.1",
                    ymin_anchor=-0.1,
                    update_y_limits=True,
                    plotid=1,
                )

            update_axes()


# ============= EOF =============================================
