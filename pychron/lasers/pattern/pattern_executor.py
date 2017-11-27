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
import cStringIO
import os
import time
from threading import Thread, current_thread, Event

from chaco.abstract_overlay import AbstractOverlay
from chaco.default_colormaps import hot
from chaco.scatterplot import render_markers
from numpy import polyfit, linspace, hstack, array, average, zeros_like, zeros, uint8, invert
from skimage.color import gray2rgb
from traits.api import Any, Bool, List

from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.view_util import open_view
from pychron.hardware.motion_controller import PositionError
from pychron.lasers.pattern.dragonfly_pattern import dragonfly
from pychron.lasers.pattern.patternable import Patternable
from pychron.paths import paths


# class PeriodCTX:
#     def __init__(self, duration):
#         self._duration = duration
#
#     def __enter__(self):
#         self._st = time.time()
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if exc_type is None:
#             et = time.time() - self._st
#             time.sleep(max(0, self._duration - et))


class CurrentPointOverlay(AbstractOverlay):
    _points = List

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        if self._points:
            with gc:
                pts = self.component.map_screen(self._points)
                render_markers(gc, pts[1:], 'circle', 3, (0, 1, 0), 1, (0, 1, 0))
                render_markers(gc, pts[:1], 'circle', 3, (1, 1, 0), 1, (1, 1, 0))

    def add_point(self, pt):
        self._points.append(pt)
        self._points = self._points[-3:]


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
        if not self.pattern:
            return

        self.start(show=self.show_patterning)
        evt = None
        if current_thread().name != 'MainThread':
            evt = Event()
            invoke_in_main_thread(self._pre_execute, evt)
            while not evt.is_set():
                time.sleep(0.05)
        else:
            self._pre_execute(evt)

        self.debug('execute xy pattern')

        xyp = self.pattern.xy_pattern_enabled
        t = None
        if xyp:
            t = Thread(target=self._execute_xy_pattern)
            t.start()

        pp = self.pattern.power_pattern
        pt = None
        if pp:
            self.debug('execute power pattern')
            pt = Thread(target=self._execute_power_pattern)
            pt.start()

        zp = self.pattern.z_pattern
        zt = None
        if zp:
            self.debug('execute z pattern')
            zt = Thread(target=self._execute_z_pattern)
            zt.start()

        if block:
            if t:
                t.join()
            if zt:
                zt.join()
            if pt:
                pt.join()

            self.finish()

    def _pre_execute(self, evt):
        self.debug('pre execute')
        pattern = self.pattern

        kind = pattern.kind
        if kind in ('SeekPattern', 'DragonFlyPeakPattern'):
            self._make_seek_graph(pattern)

        if evt is not None:
            evt.set()
        self.debug('pre execute finished')

    def _execute_power_pattern(self):
        pat = self.pattern
        self.info('starting power pattern {}'.format(pat.name))

        def func(v):
            self.laser_manager.set_laser_power(v)

        self._execute_(func, pat.power_values(), pat.power_sample, 'power pattern setpoint={value}')

    def _execute_z_pattern(self):
        pat = self.pattern
        self.info('starting power pattern {}'.format(pat.name))

        def func(v):
            self.controller.set_z(v)

        self._execute_(func, pat.z_values(), pat.z_sample, 'z pattern z={value}')

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
        self.info('starting pattern {}'.format(pat.name))
        st = time.time()
        pat.cx, pat.cy = self.controller.x, self.controller.y
        try:
            for ni in xrange(pat.niterations):
                if not self.isPatterning():
                    break

                self.info('doing pattern iteration {}'.format(ni))
                self._execute_iteration()

            self.controller.linear_move(pat.cx, pat.cy, block=True)
            if pat.disable_at_end:
                self.laser_manager.disable_device()

            self.finish()
            self.info('finished pattern: transit time={:0.1f}s'.format(time.time() - st))

        except PositionError, e:
            self.finish()
            self.controller.stop()
            self.laser_manager.emergency_shutoff(str(e))

    def _execute_iteration(self):
        controller = self.controller
        pattern = self.pattern
        if controller is not None:

            kind = pattern.kind
            if kind == 'ArcPattern':
                self._execute_arc(controller, pattern)
            elif kind == 'CircularContourPattern':

                self._execute_contour(controller, pattern)
            elif kind in ('SeekPattern', 'DragonFlyPeakPattern'):
                self._execute_seek(controller, pattern)
            # elif kind == 'DegasPattern':
            #     self._execute_lumen_degas(controller, pattern)
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

    # def _execute_lumen_degas(self, controller, pattern):
    #     from pychron.core.pid import PID
    #     from pychron.core.ui.gui import invoke_in_main_thread
    #     from pychron.lasers.pattern.mv_viewer import MVViewer
    #     from pychron.graph.stream_graph import StreamStackedGraph
    #     from pychron.mv.mv_image import MVImage
    #
    #     lm = self.laser_manager
    #     sm = lm.stage_manager
    #
    #     g = StreamStackedGraph()
    #
    #     img = MVImage()
    #
    #     img.setup_images(2, sm.get_frame_size())
    #
    #     mvviewer = MVViewer(graph=g, image=img)
    #     mvviewer.edit_traits()
    #     # g.edit_traits()
    #
    #     g.new_plot(xtitle='Time', ytitle='Lumens')
    #     g.new_series()
    #
    #     g.new_plot(xtitle='Time', ytitle='Error')
    #     g.new_series(plotid=1)
    #
    #     g.new_plot(xtitle='Time', ytitle='Power')
    #     g.new_series(plotid=2)
    #
    #     duration = pattern.duration
    #     lumens = pattern.lumens
    #     dt = pattern.period
    #     st = time.time()
    #
    #     pid = PID()
    #
    #     def update(c, e, o, cs, ss):
    #         g.record(c, plotid=0)
    #         g.record(e, plotid=1)
    #         g.record(o, plotid=2)
    #
    #         img.set_image(cs, 0)
    #         img.set_image(ss, 1)
    #
    #     while self._alive:
    #
    #         if duration and time.time() - st > duration:
    #             break
    #
    #         with PeriodCTX(dt):
    #             csrc, src, cl = sm.get_brightness()
    #
    #             err = lumens - cl
    #             out = pid.get_value(err, dt)
    #             lm.set_laser_power(out)
    #             invoke_in_main_thread(update, (cl, err, out, csrc, src))

    def _make_seek_graph(self, pattern):
        from pychron.graph.graph import Graph
        g = Graph(window_x=100, window_y=100,
                  window_title='{} - {}'.format(pattern.kind, pattern.name),
                  window_width=1000,
                  container_dict={'kind': 'h'})
        self._info = open_view(g)
        self._seek_graph = g
        return g

    def _setup_seek_graph(self, pattern):
        g = self._seek_graph

        g.new_plot(padding_right=10)
        s, p = g.new_series()
        p.aspect_ratio = 1.0
        cp = CurrentPointOverlay(component=s)
        s.overlays.append(cp)

        r = pattern.perimeter_radius
        xs = linspace(-r, r)
        xs2 = xs[::-1]
        ys = (r ** 2 - xs ** 2) ** 0.5
        ys2 = -(r ** 2 - xs2 ** 2) ** 0.5

        g.new_series(x=hstack((xs, xs2)), y=hstack((ys, ys2)), type='line')

        g.set_x_title('X (mm)', plotid=0)
        g.set_y_title('Y (mm)', plotid=0)

        # g.new_plot(padding_top=10, padding_bottom=20, padding_right=20, padding_left=60)
        # g.new_series(type='line')
        # g.new_series()
        # g.set_y_title('Density', plotid=1)
        # g.set_x_title('Time (s)', plotid=1)

        g.new_plot(padding_right=10)
        g.new_series()
        g.set_y_title('Score', plotid=1)
        g.set_x_title('Time (s)', plotid=1)

        # name = 'imagedata{:03d}'.format(i)
        # plotdata.set_data(name, ones(wh))

        imgplot = g.new_plot(padding_left=10, padding_right=10)
        imgplot.aspect_ratio = 1.0

        imgplot.x_axis.visible = False
        imgplot.y_axis.visible = False
        imgplot.x_grid.visible = False
        imgplot.y_grid.visible = False

        imgplot.data.set_data('imagedata', zeros((5, 5, 3), dtype=uint8))
        imgplot.img_plot('imagedata', colormap=hot, origin='top left')

        g.set_x_limits(-r, r)
        g.set_y_limits(-r, r)

        total_duration = pattern.total_duration
        g.set_y_limits(min_=-0.1, max_=1.1, plotid=1)
        g.set_x_limits(max_=total_duration * 1.1, plotid=1)

        # g.set_x_limits(max_=total_duration * 1.1, plotid=2)
        # g.set_y_limits(min_=-0.1, max_=1.1, plotid=2)
        return imgplot, cp

    def _setup_dragonfly_peak_graph(self, name):
        g = self._seek_graph

        def new_plot():
            # peak location
            imgplot = g.new_plot(padding_right=10)
            imgplot.aspect_ratio = 1.0
            imgplot.x_axis.visible = False
            imgplot.y_axis.visible = False
            imgplot.x_grid.visible = False
            imgplot.y_grid.visible = False

            imgplot.data.set_data('imagedata', zeros((5, 5, 3), dtype=uint8))
            imgplot.img_plot('imagedata', colormap=hot, origin='top left')
            return imgplot

        img = new_plot()
        peaks = new_plot()
        hpeaks = new_plot()

        return img, peaks, hpeaks

    def _execute_seek(self, controller, pattern):
        from pychron.core.ui.gui import invoke_in_main_thread
        # from pychron.graph.graph import Graph
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
        self.debug('Pre seek delay {}'.format(pattern.pre_seek_delay))
        time.sleep(pattern.pre_seek_delay)

        self.debug('starting seek')
        self.debug('total duration {}'.format(total_duration))
        self.debug('dwell duration {}'.format(duration))

        # if pattern.kind == 'DragonFly':
        #     imgplot, cp = self._setup_seek_graph(pattern)
        #     dragonfly(st, pattern, lm, controller, imgplot, cp)
        if pattern.kind == 'DragonFlyPeakPattern':
            self._dragonfly_peak(st, pattern, lm, controller)
        else:
            imgplot, cp = self._setup_seek_graph(pattern)
            self._hill_climber(st, controller, pattern, imgplot, cp)

        sm.canvas.show_desired_position = osdp
        invoke_in_main_thread(self._info.dispose)

    def _dragonfly_peak(self, st, pattern, lm, controller):
        imgplot, imgplot2, imgplot3 = self._setup_dragonfly_peak_graph(pattern.name)
        cx, cy = pattern.cx, pattern.cy

        sm = lm.stage_manager

        # update_axes = sm.update_axes
        # moving = sm.moving

        linear_move = controller.linear_move
        find_lum_peak = sm.find_lum_peak
        set_data = imgplot.data.set_data
        set_data2 = imgplot2.data.set_data
        set_data3 = imgplot3.data.set_data
        pr = pattern.perimeter_radius

        def validate(xx, yy):
            return (xx ** 2 + yy ** 2) ** 0.5 <= pr

        def outward_square_spiral(base):
            def gen():

                b = base
                prevx, prevy = b, 0
                while 1:
                    for cnt in xrange(4):
                        if cnt == 0:
                            x, y = b, prevy
                        elif cnt == 1:
                            x, y = prevx, b
                        elif cnt == 2:
                            x, y = prevx - b * 2, prevy
                        elif cnt == 3:
                            x, y = prevx, prevy - b * 2
                            b *= 1.1
                        prevx, prevy = x, y
                        yield x, y, 1

            return gen()

        duration = pattern.duration
        px, py = cx, cy
        series = []
        limit = -10
        point_gen = None
        while time.time() - st < pattern.total_duration:
            if not self._alive:
                break

            ist = time.time()
            pt, peaks, cpeaks, src = find_lum_peak()

            series.append(cpeaks)
            series = series[limit:]
            hpeaks = invert(array(series).sum(axis=0).clip(0, 255))

            set_data('imagedata', src)
            set_data2('imagedata', gray2rgb(peaks).astype(uint8))
            set_data3('imagedata', gray2rgb(hpeaks).astype(uint8))

            if pt is None:
                if not point_gen:
                    point_gen = outward_square_spiral(pattern.base)
                wait = False
                pt = next(point_gen)
            else:
                point_gen = None
                wait = True

            dx = pt[0] / sm.pxpermm * pt[2]
            dy = pt[1] / sm.pxpermm * pt[2]

            px = px + dx
            py = py - dy

            if validate(px - cx, py - cy):
                try:
                    linear_move(px, py, block=True, velocity=pattern.velocity,
                                use_calibration=False)
                except PositionError:
                    break

            if wait:
                et = time.time() - ist
                d = duration - et
                if d > 0:
                    time.sleep(d)

    def _hill_climber(self, st, controller, pattern, imgplot, cp):
        g = self._seek_graph
        lines = []
        cx, cy = pattern.cx, pattern.cy
        prev_xy = None
        prev_xy2 = None

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
        for i, (x, y) in enumerate(pattern.point_generator()):
            update_plot = True

            ax, ay = cx + x, cy + y
            if not self._alive:
                break

            if time.time() - st > total_duration:
                break

            # use_update_point = False
            if avg_sat_score < sat_threshold:
                # use_update_point = False
                try:
                    linear_move(ax, ay, block=True, velocity=pattern.velocity,
                                use_calibration=False,
                                update=False,
                                immediate=True)
                except PositionError:
                    break
            else:
                self.debug('Saturation target reached. not moving')
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

                set_data('imagedata', img)
                ts.append(time.time() - st)
                time.sleep(0.1)

                # while moving(force_query=True):
                #     pass
                # measure_scores(update=True)

            mt = time.time()
            while time.time() - mt < duration:
                measure_scores()

            if density_scores:
                n = len(density_scores)

                density_scores = array(density_scores)
                saturation_scores = array(saturation_scores)

                # weights = [1 / (max(0.0001, (xi - ax) ** 2 + (yi - ay) ** 2)) for xi, yi in positions]

                # avg_score = average(density_scores, weights=weights)
                # avg_sat_score = average(saturation_scores, weights=weights)
                avg_score = density_scores.mean()
                score = avg_score
                m, b = polyfit(ts, density_scores, 1)
                # if m > 0:
                #     score *= (1 + m)

                # if use_update_point:
                #     pattern.update_point(score, x, y)
                # else:
                pattern.set_point(score, x, y)
                # ff.write('{},{},{}, --- {}\n'.format(x, y, score, pattern.current_points()))
                # if prev_xy:
                #     weights = [1 / (max(0.0001, (xi - prev_xy[0]) ** 2 + (yi - prev_xy[1]) ** 2)) for xi, yi in
                #                positions]
                #     avg_score_prev = average(density_scores, weights=weights)
                #     pattern.update_point(avg_score_prev, prev_xy[0], prev_xy[1], idx=-2)
                #     if prev_xy2:
                #         weights = [1 / (max(0.0001, (xi - prev_xy2[0]) ** 2 + (yi - prev_xy2[1]) ** 2)) for xi, yi in
                #                    positions]
                #         avg_score_prev2 = average(density_scores, weights=weights)
                #         pattern.update_point(avg_score_prev2, prev_xy2[0], prev_xy2[1], idx=-3)

                # lines.append('{:0.5f}   {:0.3f}   {:0.3f}   {}    {}\n'.format(avg_score, x, y, n, score))
                self.debug('i:{} XY:({:0.5f},{:0.5f})'.format(i, x, y))
                self.debug('Density. AVG:{:0.2f} N:{} Slope:{:0.3f}'.format(avg_score, n, m))
                self.debug('Modified Density Score: {}'.format(score))
                self.debug('Saturation. AVG:{:0.2f}'.format(avg_sat_score))
                if update_plot:
                    cp.add_point((x, y))
                    g.add_datum((x, y), plotid=0)

                t = time.time() - st
                g.add_datum((t, avg_score), plotid=1)

                # g.add_bulk_data(ts, density_scores, plotid=1, series=1)

                g.add_datum((t, score),
                            ypadding='0.1',
                            ymin_anchor=-0.1,
                            update_y_limits=True, plotid=1)

            update_axes()
            # if prev_xy:
            #     prev_xy2 = prev_xy
            # prev_xy = (x, y)
            # invoke_in_main_thread(g.redraw, force=False)
            # invoke_in_main_thread(update_graph, ts, zs, z, x, y)

# ============= EOF =============================================
