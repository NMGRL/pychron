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
from chaco.abstract_overlay import AbstractOverlay
from chaco.scatterplot import render_markers
from traits.api import Any, Bool, Tuple
# ============= standard library imports ========================
import os
import cStringIO
import time
from threading import Thread
# ============= local library imports  ==========================
from pychron.envisage.view_util import open_view
from pychron.hardware.motion_controller import PositionError
from pychron.paths import paths
from pychron.lasers.pattern.patternable import Patternable


class PeriodCTX:
    def __init__(self, duration):
        self._duration = duration

    def __enter__(self):
        self._st = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            et = time.time() - self.st
            time.sleep(max(0, self._duration - et))


class CurrentPointOverlay(AbstractOverlay):
    point = Tuple((0, 0))

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            pts = self.component.map_screen([self.point])
            render_markers(gc, pts, 'circle', 3, 'green', 1, 'green')


class PatternExecutor(Patternable):
    """
         a pattern is only good for one execution.
         self.pattern needs to be reset after stop or finish using load_pattern(name_or_pickle)
    """
    controller = Any
    laser_manager = Any
    show_patterning = Bool(False)
    _alive = Bool(False)
    _next_point = None
    pattern = None

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
            wfile = open(path, 'rb')
        else:
            # convert name_or_pickle into a file like obj
            wfile = cStringIO.StringIO(name_or_pickle)

        # self._load_pattern sets self.pattern
        pattern = self._load_pattern(wfile, path)

        self.on_trait_change(self.stop, 'canceled')
        return pattern

    def is_local_pattern(self, name):

        def test_name(ni):
            path = os.path.join(paths.pattern_dir, ni)
            if os.path.isfile(path):
                return path

        for ni in (name, name + '.lp'):
            p = test_name(ni)
            if p:
                return p

    def stop(self):
        self._alive = False
        if self.controller:
            self.info('User requested stop')
            self.controller.stop()

        if self.pattern is not None:
            if self.controller:
                self.controller.linear_move(self.pattern.cx, self.pattern.cy)
            # self.pattern.close_ui()
            self.info('Pattern {} stopped'.format(self.pattern_name))

            # prevent future stops (AbortJogs from massspec) from executing
            self.pattern = None

    def isPatterning(self):
        return self._alive

    def close_pattern(self):
        pass

    def show_pattern(self):
        self.pattern.window_x = 50
        self.pattern.window_y = 50
        open_view(self.pattern, view='graph_view')

    def execute(self, block=False):
        """
            if block is true wait for patterning to finish
            before returning
        """
        self.start(show=self.show_patterning)

        t = Thread(target=self._execute)
        t.start()

        if block:
            t.join()

            self.finish()

    def _execute(self):
        pat = self.pattern
        if pat:
            # self.info('enabling laser')
            # self.laser_manager.enable_device(clear_setpoint=False)

            self.info('starting pattern {}'.format(pat.name))
            st = time.time()
            pat.cx, pat.cy = self.controller.x, self.controller.y
            try:
                for ni in xrange(pat.niterations):
                    if not self.isPatterning():
                        break

                    self.info('doing pattern iteration {}'.format(ni))
                    self._execute_iteration()

                self.controller.linear_move(pat.cx, pat.cy)
                if pat.disable_at_end:
                    self.laser_manager.disable_device()
                self.finish()
                self.info('finished pattern: transit time={:0.1f}s'.format(time.time() - st))

            except PositionError, e:
                self.finish()
                # self.laser_manager.disable_device()
                self.controller.stop()
                self.laser_manager.emergency_shutoff(str(e))
                # self.warning(str(e))

    def _execute_iteration(self):
        controller = self.controller
        pattern = self.pattern
        if controller is not None:

            kind = pattern.kind
            if kind == 'ArcPattern':
                self._execute_arc(controller, pattern)
            elif kind == 'CircularContourPattern':

                self._execute_contour(controller, pattern)
            elif kind == 'SeekPattern':
                self._execute_seek(controller, pattern)
            elif kind == 'DegasPattern':
                self._execute_lumen_degas(controller, pattern)
            else:
                self._execute_points(controller, pattern, multipoint=False)

    def _execute_points(self, controller, pattern, multipoint=False):
        pts = pattern.points_factory()
        if multipoint:
            controller.multiple_point_move(pts, velocity=pattern.velocity)
        else:
            for x, y in pts:
                if not self.isPatterning():
                    break
                controller.linear_move(x, y, block=True,
                                       velocity=pattern.velocity)

    def _execute_contour(self, controller, pattern):
        for ni in range(pattern.nsteps):
            if not self.isPatterning():
                break

            r = pattern.radius * (1 + ni * pattern.percent_change)
            self.info('doing circular contour {} {}'.format(ni + 1, r))
            controller.single_axis_move('x', pattern.cx + r,
                                        block=True)
            controller.arc_move(pattern.cx, pattern.cy, 360,
                                block=True)
            time.sleep(0.1)

    def _execute_arc(self, controller, pattern):
        controller.single_axis_move('x', pattern.radius, block=True)
        controller.arc_move(pattern.cx, pattern.cy, pattern.degrees, block=True)

    def _execute_lumen_degas(self, controller, pattern):
        from pychron.core.pid import PID
        from pychron.core.ui.gui import invoke_in_main_thread
        from pychron.lasers.pattern.mv_viewer import MVViewer
        from pychron.graph.stream_graph import StreamStackedGraph
        from pychron.mv.mv_image import MVImage

        lm = self.laser_manager
        sm = lm.stage_manager

        g = StreamStackedGraph()

        img = MVImage()

        img.setup_images(2, sm.get_frame_size())

        mvviewer = MVViewer(graph=g, image=img)
        mvviewer.edit_traits()
        # g.edit_traits()

        g.new_plot(xtitle='Time', ytitle='Lumens')
        g.new_series()

        g.new_plot(xtitle='Time', ytitle='Error')
        g.new_series(plotid=1)

        g.new_plot(xtitle='Time', ytitle='Power')
        g.new_series(plotid=2)

        duration = pattern.duration
        lumens = pattern.lumens
        dt = pattern.period
        st = time.time()

        pid = PID()

        def update(c, e, o, cs, ss):
            g.record(c, plotid=0)
            g.record(e, plotid=1)
            g.record(o, plotid=2)

            img.set_image(cs, 0)
            img.set_image(ss, 1)

        while self._alive:

            if duration and time.time() - st > duration:
                break

            with PeriodCTX(dt):
                csrc, src, cl = sm.get_brightness()

                err = lumens - cl
                out = pid.get_value(err, dt)
                lm.set_laser_power(out)
                invoke_in_main_thread(update, (cl, err, out, csrc, src))

    def _execute_seek(self, controller, pattern):
        from pychron.core.ui.gui import invoke_in_main_thread
        from pychron.graph.graph import Graph

        duration = pattern.duration
        g = Graph()
        g.edit_traits()
        g.new_plot()
        s, p = g.new_series()

        g.new_plot()
        g.new_series(type='line')

        cp = CurrentPointOverlay(component=s)
        s.overlays.append(cp)
        w = 2
        g.set_x_limits(-w, w)
        g.set_y_limits(-w, w)
        om = 60
        g.set_x_limits(max_=om, plotid=1)

        lm = self.laser_manager
        sm = lm.stage_manager

        st = time.time()

        def update_graph(zs, zz, xx, yy):
            cp.point = (xx, yy)
            g.add_datum((xx, yy), plotid=0)
            t = time.time() - st
            g.add_datum((t, zz),
                        update_y_limits=True,
                        plotid=1)

            g.add_datum((t,) * len(zs), zs,
                        update_y_limits=True,
                        plotid=1, series=1)
            g.set_x_limits(max_=max(om, t + 10), plotid=1)
            g.redraw()

        pp = os.path.join(paths.data_dir, 'seek_pattern.txt')
        with open(pp, 'w') as wfile:
            cx, cy = pattern.cx, pattern.cy
            wfile.write('{},{}\n'.format(cx, cy))
            wfile.write('#z,     x,     y,     n\n')
            gen = pattern.point_generator()
            for x, y in gen:
                if not self._alive:
                    break

                with PeriodCTX(1):
                    # x, y = gen.next()
                    # x, y = pattern.next_point
                    controller.linear_move(cx + x, cy + y, block=False, velocity=pattern.velocity)

                    mt = time.time()
                    zs = []
                    while sm.moving():
                        _, _, v = sm.get_brightness()
                        zs.append(v)

                    while 1:
                        if time.time() - mt > duration:
                            break
                        _, _, v = sm.get_brightness()
                        zs.append(v)

                    if zs:
                        n = len(zs)
                        z = sum(zs) / float(n)
                        self.debug('XY:({},{}) Z:{}, N:{}'.format(x, y, z, n))
                        pattern.set_point(z, x, y)

                        wfile.write('{:0.5f},{:0.3f},{:0.3f},{}\n'.format(z, x, y, n))

                        invoke_in_main_thread(update_graph, zs, z, x, y)
        g.close_ui()
        # if len(triangle) < 3:
        #     z = lm.get_brightness()
        #     triangle.append((z, x, y))
        # else:
        #     nx,ny = triangulator(triangle)


        # def _execute_seek(self, controller, pattern):
        #
        #     # =======================================================================
        #     # monitor input
        #     # =======================================================================
        #     def _monitor_input(pevt, fevt, threshold=1, deadband=0.5, period=0.25):
        #         """
        #             periodically get input value
        #             if input value greater than threshold set pause event
        #             if input value last than threshold-deadband and was paused, clear paused flag
        #         """
        #         get_value = lambda: 1
        #         flag = False
        #         while not fevt.is_set() and self.isPatterning():
        #             v = get_value()
        #             if v > threshold:
        #                 pevt.set()
        #                 flag = True
        #             elif flag and v < (threshold - deadband):
        #                 pevt.clear()
        #                 flag = False
        #             time.sleep(period)
        #
        #     # =======================================================================
        #     # control motion
        #     # =======================================================================
        #     """
        #         if paused and not already stopped, stop motion
        #         if not paused not but was paused move to newt_point
        #     """
        #
        #     def _control_motion(self, pevt, fevt, q):
        #         flag = False
        #         while not fevt.is_set() and self.isPatterning():
        #             if pevt.is_set():
        #                 if not flag:
        #                     flag = True
        #                     controller.stop()
        #                 time.sleep(0.1)
        #
        #             else:
        #                 if flag:
        #                     try:
        #                         np = q.get_nowait()
        #                         controller.linear_move(*np, block=False,
        #                                                velocity=pattern.velocity)
        #                     except Empty:
        #                         self.debug('No next point avaliable')
        #                     flag = False
        #
        #                 time.sleep(0.1)
        #
        #     finished = Event()
        #     paused = Event()
        #     q = Queue()
        #     mt = Thread(target=_monitor_input,
        #                 args=(paused, finished),
        #                 name='seek.monitor_input')
        #
        #     ct = Thread(target=_control_motion,
        #                 args=(paused, finished, q),
        #                 name='seek.monitor_input')
        #     mt.start()
        #     ct.start()
        #
        #     duration = 10
        #     st = time.time()
        #     while 1:
        #
        #         if time.time() - st > duration:
        #             break
        #
        #         x, y = pattern.next_point()
        #         # pts = pattern.points_factory()
        #         # for x, y in pts:
        #         #     if not self.isPatterning():
        #         #         break
        #
        #         q.put((x, y))
        #         controller.linear_move(x, y, block=True,
        #                                velocity=pattern.velocity)
        #
        #     finished.set()

# ============= EOF =============================================
