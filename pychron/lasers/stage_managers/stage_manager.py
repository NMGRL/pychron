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

#=============enthought library imports=======================
from traits.api import DelegatesTo, Property, Instance, \
    Button, List, String, Event, Bool
from traitsui.api import View, Item, HGroup, VGroup, spring, \
    EnumEditor
# from apptools.preferences.preference_binding import bind_preference
#=============standard library imports =======================
import os
# from threading import Thread
import time
from numpy import array, asarray
#=============local library imports  ==========================
from pychron.experiment.utilities.position_regex import POINT_REGEX, XY_REGEX, TRANSECT_REGEX
from pychron.managers.manager import Manager
from pychron.canvas.canvas2D.laser_tray_canvas import LaserTrayCanvas
# from pychron.core.helpers.color_generators import colors8i as colors

from pychron.hardware.motion_controller import MotionController
from pychron.paths import paths
import pickle
# from pychron.lasers.stage_managers.stage_visualizer import StageVisualizer
from pychron.lasers.points.points_programmer import PointsProgrammer
# from pychron.core.geometry.scan_line import make_scan_lines
from pychron.core.geometry.geometry import sort_clockwise
from pychron.core.geometry.convex_hull import convex_hull
from pychron.core.geometry.polygon_offset import polygon_offset
from pychron.lasers.stage_managers.calibration.tray_calibration_manager import TrayCalibrationManager
from pychron.core.ui.stage_component_editor import LaserComponentEditor
from pychron.core.ui.thread import Thread
from pychron.core.ui.preference_binding import bind_preference, ColorPreferenceBinding

from pychron.managers.motion_controller_managers.motion_controller_manager \
    import MotionControllerManager
# from tray_calibration_manager import TrayCalibrationManager
# from stage_component_editor import LaserComponentEditor
# from pychron.canvas.canvas2D.markup.markup_items import CalibrationItem
# from pattern.pattern_manager import PatternManager
from stage_map import StageMap


class StageManager(Manager):
    """
    """
    stage_controller_class = String('Newport')

    stage_controller = Instance(MotionController)
    points_programmer = Instance(PointsProgrammer)
    motion_controller_manager = Instance(MotionControllerManager)
    canvas = Instance(LaserTrayCanvas)
    _stage_map = Instance(StageMap)

    simulation = DelegatesTo('stage_controller')
    stage_map_klass = StageMap
    stage_map = Property(depends_on='_stage_map')
    stage_maps = Property(depends_on='_stage_maps')

    _stage_maps = List
    #===========================================================================
    # buttons
    #===========================================================================
    home = Button('home')
    home_option = String('Home All')
    home_options = List

    ejoystick = Event
    joystick_label = String('Enable Joystick')
    joystick = Bool(False)
    joystick_timer = None

    #    buttons = List([('home', None, None),
    # #                    ('jog', 'jog_label', None),
    #                    ('stop_button', 'stop_label', None)
    #                      ])

    back_button = Button
    stop_button = Button('Stop')

    canvas_editor_klass = LaserComponentEditor

    tray_calibration_manager = Instance(TrayCalibrationManager)

    #     motion_profiler = DelegatesTo('stage_controller')

    #     visualizer = Instance(StageVisualizer)

    move_thread = None
    temp_position = None
    temp_hole = None
    linear_move_history = List

    keyboard_focus = Event

    #    calibrated_position_entry = Property(String(enter_set=True, auto_set=False))
    #    _calibrated_position = Str
    calibrated_position_entry = String(enter_set=True, auto_set=False)

    use_modified = Bool(True)  # set true to use modified affine calculation
    use_autocenter = Bool

    def __init__(self, *args, **kw):
        """

        """
        super(StageManager, self).__init__(*args, **kw)
        #        self.add_output('Welcome')
        self.stage_controller = self._stage_controller_factory()

    #    def opened(self, ui):
    #        self.keyboard_focus = True
    #        super(StageManager, self).opened(ui)
    def create_device(self, *args, **kw):
        dev = super(StageManager, self).create_device(*args, **kw)
        dev.parent = self
        return dev

    def goto_position(self, v):
        if XY_REGEX[0].match(v):
            self._move_to_calibrated_position(v)
        elif POINT_REGEX.match(v) or TRANSECT_REGEX[0].match(v):
            self.move_to_point(v)

        else:
            self.move_to_hole(v)
    def is_auto_correcting(self):
        return False

    def kill(self):
        r = super(StageManager, self).kill()

        p = os.path.join(paths.hidden_dir, 'stage_map')
        self.info('saving stage_map {} to {}'.format(self.stage_map, p))
        with open(p, 'wb') as f:
            pickle.dump(self.stage_map, f)
        return r

    def bind_preferences(self, pref_id):
        bind_preference(self.canvas, 'show_grids', '{}.show_grids'.format(pref_id))
        bind_preference(self.canvas, 'show_laser_position', '{}.show_laser_position'.format(pref_id))
        bind_preference(self.canvas, 'show_desired_position', '{}.show_laser_position'.format(pref_id))
        bind_preference(self.canvas, 'desired_position_color', '{}.desired_position_color'.format(pref_id),
                        factory=ColorPreferenceBinding)
        #        bind_preference(self.canvas, 'render_map', '{}.render_map'.format(pref_id))
        #
        bind_preference(self.canvas, 'crosshairs_kind', '{}.crosshairs_kind'.format(pref_id))
        bind_preference(self.canvas, 'crosshairs_color',
                        '{}.crosshairs_color'.format(pref_id),
                        factory=ColorPreferenceBinding)
        bind_preference(self.canvas, 'crosshairs_radius', '{}.crosshairs_radius'.format(pref_id))
        bind_preference(self.canvas, 'crosshairs_offsetx', '{}.crosshairs_offsetx'.format(pref_id))
        bind_preference(self.canvas, 'crosshairs_offsety', '{}.crosshairs_offsety'.format(pref_id))
        #
        bind_preference(self.canvas, 'scaling', '{}.scaling'.format(pref_id))
        #
        #        bind_preference(self.tray_calibration_manager, 'style', '{}.calibration_style'.format(pref_id))
        bind_preference(self.canvas, 'show_bounds_rect',
                        '{}.show_bounds_rect'.format(pref_id))

        self.canvas.request_redraw()

    def load(self):
        self._stage_maps = []
        config = self.get_configuration()
        # load the stage maps
        mapfiles = self.config_get(config, 'General', 'mapfiles')
        for mapfile in mapfiles.split(','):
            path = os.path.join(paths.map_dir, mapfile.strip())
            sm = StageMap(file_path=path)
            sm.load_correction_file()
            self._stage_maps.append(sm)

        # load user points as stage map
        for di in os.listdir(paths.user_points_dir):
            if di.endswith('.yaml'):
                path = os.path.join(paths.user_points_dir, di)
                sm = self.stage_map_klass(file_path=path)
                self._stage_maps.append(sm)

        # load the saved stage map
        sp = self._get_stage_map_by_name(self._load_previous_stage_map())
        if sp is not None:
            sm = sp

        self._stage_map = sm
        self.points_programmer.load_stage_map(sm)

        # load the calibration file
        # should have calibration files for each stage map
        self.tray_calibration_manager.load_calibration()

        # load the points file
        # self.canvas.load_points_file(self.points_file)

        # load defaults
        self._default_z = self.config_get(config, 'Defaults', 'z', default=13, cast='float')

        self.canvas.set_map(sm)
        self.canvas.request_redraw()

    #    def finish_loading(self):
    #        self.initialize_stage()

    def initialize_stage(self):
        self.update_axes()
        axes = self.stage_controller.axes
        self.home_options = ['Home All', 'XY'] + sorted([axes[a].name.upper() for a in axes])
        self.canvas.parent = self

    def save_calibration(self, name):
        self.tray_calibration_manager.save_calibration(name=name)

    def add_stage_map(self, v):
        sm = self.stage_map_klass(file_path=v)
        psm = self._get_stage_map_by_name(sm.name)
        if psm:
            self._stage_maps.remove(psm)

        self._stage_maps.append(sm)

    def accept_point(self):
        self.points_programmer.accept_point()

    def get_stage_map(self):
        """
            return current StageMap object
            different than self.stage_map. self.stage_map returns the "name" of the current stage map
        """
        return self._stage_map

    def set_stage_map(self, v):
        return self._set_stage_map(v)

    def single_axis_move(self, *args, **kw):
        return self.stage_controller.single_axis_move(*args, **kw)

    def linear_move(self, x, y, use_calibration=True,
                    check_moving=False, abort_if_moving=False, **kw):

        if check_moving:
            if self.moving():
                self.warning('MotionController already in motion')
                if abort_if_moving:
                    self.warning('Move to {},{} aborted'.format(x,y))
                    return
                else:
                    self.stop()
                    self.debug('Motion stopped. moving to {},{}'.format(x,y))

        cpos = self.get_uncalibrated_xy()
        self.linear_move_history.append((cpos, {}))
        pos = (x, y)
        if use_calibration:
            pos = self.get_calibrated_position(pos)
            f = lambda x: '{:0.5f},{:0.5f}'.format(*x)
            self.debug('%%%%%%%%%%%%%%%%% mapped {} to {}'.format(f((x, y)), f(pos)))

        self.stage_controller.linear_move(*pos, **kw)

    def move_to_hole(self, hole, **kw):
        self._move(self._move_to_hole, hole, name='move_to_hole', **kw)

    def move_to_point(self, pt):
        self._move(self._move_to_point, pt, name='move_to_point')

    def move_polyline(self, line):
        self._move(self._move_to_line, line, name='move_to_line')

    def move_polygon(self, poly):
        self._move(self._move_polygon, poly, name='move_polygon')

    def drill_point(self, pt):
        self._move(self._drill_point, pt, name='drill_point')

    def set_x(self, value, **kw):
        return self.stage_controller.single_axis_move('x', value, **kw)

    def set_y(self, value, **kw):
        return self.stage_controller.single_axis_move('y', value, **kw)

    def set_z(self, value, **kw):
        return self.stage_controller.single_axis_move('z', value, **kw)

    def set_xy(self, x, y, **kw):
        hole = self._get_hole_by_position(x, y)
        if hole:
            self.move_to_hole(hole)
        #            self._set_hole(hole.id)
        # self.move_to_hole(hole.id)
        #            self._set_hole(hole.id)
        else:
            return self.linear_move(x, y, **kw)

    def get_hole(self, name):
        if self._stage_map:
            return self._stage_map.get_hole(name)
            #
            #    def do_pattern(self, patternname):
            #        return self.pattern_manager.execute_pattern(patternname)

    def update_axes(self, update_hole=True):
        """
        """
        self.info('querying axis positions')
        self.stage_controller.update_axes()

    #        if update_hole:
    #            #check to see if we are at a hole
    #            hole = self.get_calibrated_hole(self.stage_controller._x_position,
    #                                              self.stage_controller._y_position,
    #                                              )
    #            if hole is not None:
    #                self._hole = str(hole.id)

    def move_to_load_position(self):
        """
        """
        x, y, z = self.stage_controller.get_load_position()
        self.info('moving to load position, x={}, y={}, z={}'.format(x, y, z))

        self.stage_controller.linear_move(x, y, grouped_move=False, block=False)

        self.stage_controller.set_z(z)
        self.stage_controller.block()

    def stop(self, ax_key=None, verbose=False):
        self._stop(ax_key, verbose)

    def relative_move(self, *args, **kw):
        self.stage_controller.relative_move(*args, **kw)

    def moving(self, force_query=False, **kw):
        moving = False
        if self.stage_controller.timer is not None:
            moving = self.stage_controller.timer.isActive()
        elif force_query:
            moving = self.stage_controller._moving_(**kw)

        return moving

    def define_home(self, **kw):
        self.stage_controller.define_home(**kw)

    def get_z(self):
        return self.stage_controller._z_position

    def get_uncalibrated_xy(self, pos=None):
        if pos is None:
            pos = (self.stage_controller.x, self.stage_controller.y)
            if self.stage_controller.xy_swapped():
                pos = pos[1], pos[0]

        canvas = self.canvas
        ca = canvas.calibration_item
        if ca:
            pos = self._stage_map.map_to_uncalibration(pos,
                                                       ca.center,
                                                       ca.rotation,
                                                       ca.scale)

        return pos

    def get_calibrated_xy(self):
        pos = (self.stage_controller._x_position, self.stage_controller._y_position)
        if self.stage_controller.xy_swapped():
            pos = pos[1], pos[0]

        pos = self.canvas.map_offset_position(pos)
        return self.get_calibrated_position(pos)

    def get_calibrated_position(self, pos, key=None):
        smap = self._stage_map

        # use a affine transform object to map
        canvas = self.canvas
        ca = canvas.calibration_item
        if ca:
            rot = ca.rotation
            cpos = ca.center
            scale = ca.scale

            self.debug('Calibration parameters: rot={:0.3f}, cpos={} scale={:0.3f}'.format(rot, cpos, scale))
            pos = smap.map_to_calibration(pos, cpos, rot,
                                          scale=scale,
                                          use_modified=self.use_modified)

        return pos

    def get_calibrated_hole(self, x, y):
        ca = self.canvas.calibration_item
        if ca is not None:
            smap = self._stage_map

            rot = ca.rotation
            cpos = ca.center

            def _filter(hole, x, y, tol=0.1):
                cx, cy = smap.map_to_calibration((hole.x, hole.y), cpos, rot)
                return abs(cx - x) < tol and abs(cy - y) < tol

            return next((si for si in smap.sample_holes
                         if _filter(si, x, y)
                        ), None)


            #    def _hole_changed(self):
            #        self._set_hole(self.hole)

    def _load_previous_stage_map(self):
        p = os.path.join(paths.hidden_dir, 'stage_map')

        if os.path.isfile(p):
            self.info('loading previous stage map')
            with open(p, 'rb') as f:
                try:
                    return pickle.load(f)
                except pickle.PickleError:
                    pass

    def _home(self):
        """
        """
        #        define_home = True
        if self.home_option == 'Home All':

            msg = 'homing all motors'
            homed = ['x', 'y', 'z']
            home_kwargs = dict(x=-25, y=-25, z=50)

        elif self.home_option == 'XY':
            msg = 'homing x,y'
            homed = ['x', 'y']
            home_kwargs = dict(x=-25, y=-25)
        else:
        #            define_home =
            msg = 'homing {}'.format(self.home_option)
            home_kwargs = {self.home_option: -25 if self.home_option in ['X', 'Y'] else 50}
            homed = [self.home_option.lower().strip()]

        self.info(msg)

        # if define_home:
        self.stage_controller.set_home_position(**home_kwargs)

        self.stage_controller.home(homed)

        # explicitly block
        #        self.stage_controller.block()

        if 'z' in homed and 'z' in self.stage_controller.axes:
        # will be a positive limit error in z
        #            self.stage_controller.read_error()

            time.sleep(1)
            self.info('setting z to nominal position. {} mm '.format(self._default_z))
            self.stage_controller.single_axis_move('z', self._default_z,
                                                   block=True)
            self.stage_controller._z_position = self._default_z

        if self.home_option in ['XY', 'Home All']:
            time.sleep(0.25)

            # the stage controller should  think x and y are at -25,-25
            self.stage_controller._x_position = -25
            self.stage_controller._y_position = -25

            self.info('moving to center')
            self.stage_controller.linear_move(0, 0, block=True,
                                              sign_correct=False)

    def _get_hole_by_position(self, x, y):
        if self._stage_map:
            return self._stage_map._get_hole_by_position(x, y)

    def _get_hole_by_name(self, key):
        sm = self._stage_map
        return sm.get_hole(key)

    # ===============================================================================
    # special move
    # ===============================================================================
    def _stop(self, ax_key=None, verbose=False):
        self.stage_controller.stop(ax_key=ax_key, verbose=verbose)
        if self.parent.pattern_executor:
            self.parent.pattern_executor.stop()

    def _move(self, func, pos, name=None, *args, **kw):
        if pos is None:
            return

        if self.move_thread and self.move_thread.isRunning():
            self.stage_controller.stop()
        if name is None:
            name = func.func_name

        self.move_thread = Thread(name='stage.{}'.format(name),
                                  target=func, args=(pos,) + args, kwargs=kw)
        self.move_thread.start()

    def _drill_point(self, pt):
        zend = pt.zend
        vel = pt.velocity

        # assume already at zstart
        st = time.time()
        self.info('start drilling. move to {}. velocity={}'.format(zend, vel))
        self.set_z(zend, velocity=vel, block=True)
        et = time.time() - st

        self.info('drilling complete. drilled for {}s'.format(et))

    def _move_polygon(self, pts, velocity=5,
                      offset=50,
                      use_outline=True,
                      find_min=False,
                      scan_size=None,
                      use_move=True,
                      use_convex_hull=True,
                      motors=None,
                      verbose=True,
                      start_callback=None, end_callback=None):
        '''
            motors is a dict of motor_name:value pairs
        '''
        if pts is None:
            return

        if not isinstance(pts, list):
            velocity = pts.velocity
            use_convex_hull = pts.use_convex_hull
            if scan_size is None:
                scan_size = pts.scan_size
            use_outline = pts.use_outline
            offset = pts.offset
            find_min = pts.find_min
            pts = [dict(xy=(pi.x, pi.y), z=pi.z, ) for pi in pts.points]

        # set motors
        if motors is not None:
            for k, v in motors.itervalues():
                '''
                    motor will not set if it has been locked using set_motor_lock or
                    remotely using SetMotorLock
                '''
                if use_move:
                    self.parent.set_motor(k, v, block=True)

        xy = [pi['xy'] for pi in pts]
        n = 1000
        if scan_size is None:
            scan_size = n / 2

        # convert points to um
        pts = array(xy)
        pts *= n
        pts = asarray(pts, dtype=int)
        '''
            sort clockwise ensures consistent offset behavior
            a polygon gain have a inner or outer sense depending on order of vertices

            always use sort_clockwise prior to any polygon manipulation
        '''
        pts = sort_clockwise(pts, pts)

        sc = self.stage_controller
        sc.set_program_mode('absolute')
        # do smooth transitions between points
        sc.set_smooth_transitions(True)

        if use_convex_hull:
            pts = convex_hull(pts)

        if use_outline:
            # calculate new polygon
            offset_pts = polygon_offset(pts, -offset)
            offset_pts = array(offset_pts, dtype=int)
            # polygon offset used 3D vectors.
            # trim to only x,y
            pts = offset_pts[:, (0, 1)]

            # trace perimeter
            if use_move:
                p0 = xy[0]
                self.linear_move(p0[0], p0[1], mode='absolute', block=True)

                sc.timer = sc.timer_factory()

                if start_callback is not None:
                    start_callback()

                #                buf=[]
                for pi in xy[1:]:
                    self.linear_move(pi[0], pi[1],
                                     velocity=velocity,
                                     mode='absolute', set_stage=False)

                # finish at first point
                self.linear_move(p0[0], p0[1],
                                 velocity=velocity,
                                 mode='absolute', set_stage=False)

                sc.block()
                self.info('polygon perimeter trace complete')
                '''
                    have the oppurtunity here to turn off laser and change parameters i.e mask
                '''
        if use_move:
            # calculate and step thru scan lines
            self._raster(pts, velocity,
                         step=scan_size,
                         scale=n,
                         find_min=find_min,
                         start_callback=start_callback, end_callback=end_callback,
                         verbose=verbose)

        sc.set_program_mode('relative')
        if end_callback is not None:
            end_callback()
        self.info('polygon raster complete')

    def _raster(self, points, velocity,
                step=500,
                scale=1000,
                find_min=False,
                start_callback=None, end_callback=None, verbose=False):

        from pychron.core.geometry.scan_line import raster

        lines = raster(points, step=step, find_min=find_min)

        # initialize variables
        cnt = 0
        direction = 1
        flip = False
        lasing = False
        sc = self.stage_controller

        if verbose:
            self.info('start raster')

        #        print lines
        # loop thru each scan line
        #        for yi, xs in lines[::skip]:
        for yi, xs in lines:
            if direction == -1:
                xs = list(reversed(xs))

            # convert odd numbers lists to even
            n = len(xs)
            if n % 2 != 0:
                xs = sorted(list(set(xs)))

            # traverse each x-intersection pair
            n = len(xs)
            for i in range(0, n, 2):
                if len(xs) <= 1:
                    continue

                x1, x2, yy = xs[i] / scale, xs[i + 1] / scale, yi / scale
                if abs(x1 - x2) > 1e-10:
                    if not lasing:
                        if verbose:
                            self.info('fast to {} {},{}'.format(cnt, x1, yy))

                        self.linear_move(x1, yy,
                                         mode='absolute', set_stage=False,
                                         block=True)
                        if start_callback is not None:
                            start_callback()

                        lasing = True
                    else:
                        if verbose:
                            self.info('slow to {} {},{}'.format(cnt, x1, yy))

                        sc.timer = sc.timer_factory()
                        self.linear_move(x1, yy,
                                         mode='absolute', set_stage=False,
                                         velocity=velocity)

                    if verbose:
                        self.info('move to {}a {},{}'.format(cnt, x2, yy))

                        #                if n > 2 and not i * 2 >= n:
                    # line this scan line has more then 1 segment turn off laser at end of segment
                    if i + 2 < n and not xs[i + 1] == xs[i + 2]:
                        self.linear_move(x2, yy, velocity=velocity,
                                         mode='absolute', set_stage=False,
                                         block=True)
                        self.info('wait for move complete')
                        if end_callback is not None:
                            end_callback()

                        lasing = False
                    else:
                        self.linear_move(x2, yy, velocity=velocity,
                                         mode='absolute', set_stage=False,
                        )
                    cnt += 1
                    flip = True
                else:
                    flip = False

            if flip:
                direction *= -1

        sc.block()
        if verbose:
            self.info('end raster')


    def _move_polyline(self, pts, start_callback=None, end_callback=None):
        if not isinstance(pts, list):
            segs = pts.velocity_segments
            segs = segs[:1] + segs
            pts = [dict(xy=(pi.x, pi.y), z=pi.z, velocity=vi) for vi, pi in
                   zip(segs, pts.points)]

        sc = self.stage_controller
        self.linear_move(pts[0]['xy'][0], pts[0]['xy'][1],
                         update_hole=False,
                         use_calibration=False,
                         block=True)
        sc.set_z(pts[0]['z'], block=True)

        cpos = dict()
        # set motors
        for motor in ('mask', 'attenuator'):
            if pts[0].has_key(motor):
                self.parent.set_motor(motor, pts[0][motor])
                cpos[motor] = pts[0][motor]

        sc.set_program_mode('absolute')
        sc.timer = sc.timer_factory()
        if start_callback:
            start_callback()

        npts = pts[1:]
        setmotors = dict()
        for i, di in enumerate(npts):
            xi, yi, zi, vi = di['xy'][0], di['xy'][1], di['z'], di['velocity']
            sc.set_z(zi)

            block = False
            for motor in ('mask', 'attenuator'):
                # fix next step sets motor should block
                if i + 1 < len(npts):
                    dii = npts[i + 1]
                    if dii.has_key(motor):
                        if dii[motor] != cpos[motor]:
                            m = self.parent.get_motor(motor)
                            if not m.locked:
                                block = True
                                setmotors[motor] = dii[motor]

            self.linear_move(xi, yi, velocity=vi,
                             block=block,
                             mode='absolute', # use absolute mode because commands are queued
                             set_stage=False)
            if block:
                if end_callback:
                    end_callback()

                for k, v in setmotors.iteritems():
                    self.parent.set_motor(k, v, block=True)

                if start_callback:
                    start_callback()

        # wait until motion complete
        sc.block()
        if end_callback:
            end_callback()

        sc.set_program_mode('relative')

    #        if start and smooth:
    #            sc.execute_command_buffer()
    #            sc.end_command_buffer()

    #    def start_enqueued(self):
    #        sc = self.stage_controller
    #        sc.execute_command_buffer()
    #        sc.end_command_buffer()

    def _move_to_point(self, pt):
        self.debug('move to point={}'.format(pt))
        if isinstance(pt, str):
            pt = self.canvas.get_point(pt)

        self.debug('move to point canvas pt={}'.format(pt))
        if pt is not None:
            pos = pt.x, pt.y

            self.info('Move to point {}: {:0.5f},{:0.5f},{:0.5f}'.format(pt.identifier,
                                                                         pt.x, pt.y, pt.z))
            self.stage_controller.linear_move(block=True, *pos)

            if hasattr(pt, 'z'):
                self.stage_controller.set_z(pt.z, block=True)

            self.debug('Not setting motors for pt')
            #self.parent.set_motors_for_point(pt)

            self._move_to_point_hook()

        self.info('Move complete')
        self.update_axes()

    def _move_to_hole(self, key, correct_position=True):
        self.info('Move to hole {} type={}'.format(key, str(type(key))))
        self.temp_hole = key
        self.temp_position = self._stage_map.get_hole_pos(key)

        pos = self._stage_map.get_corrected_hole_pos(key)
        self.info('position {}'.format(pos))
        if pos is not None:
        #             self.visualizer.set_current_hole(key)

            if abs(pos[0]) < 1e-6:
                pos = self._stage_map.get_hole_pos(key)
                # map the position to calibrated space
                pos = self.get_calibrated_position(pos, key=key)
            else:
                # check if this is an interpolated position
                # if so probably want to do an autocentering routine
                hole = self._stage_map.get_hole(key)
                if hole.interpolated:
                    self.info('using an interpolated value')
                else:
                    self.info('using previously calculated corrected position')
            self.stage_controller.linear_move(block=True, *pos)
            #            if self.tray_calibration_manager.calibration_style == 'MassSpec':
            if not self.tray_calibration_manager.isCalibrating():
                self._move_to_hole_hook(key, correct_position)
            else:
                self._move_to_hole_hook(key, correct_position)

            self.info('Move complete')
            self.update_axes()  # update_hole=False)

            #        self.move_thread = None

    def _move_to_hole_hook(self, *args):
        pass

    def _move_to_point_hook(self):
        pass


    # ===============================================================================
    # Views
    # ===============================================================================
    #    def edit_traits(self, *args, **kw):
    #        self.initialize_stage()
    #        return super(StageManager, self).edit_traits(*args, **kw)




    # ===============================================================================

    # ===============================================================================
    # Property Get / Set
    # ===============================================================================

    def _get_stage_maps(self):
        if self._stage_maps:
            return [s.name for s in self._stage_maps]
        else:
            return []

    def _get_stage_map(self):
        if self._stage_map:
            return self._stage_map.name

    def _get_stage_map_by_name(self, name):
        return next((sm for sm in self._stage_maps if sm.name == name), None)

    def _set_stage_map(self, v):
        s = self._get_stage_map_by_name(v)
        if s is not None:
            self.info('setting stage map to {}'.format(v))
            self._stage_map = s

            self.canvas.set_map(s)
            self.tray_calibration_manager.load_calibration(stage_map=s.name)
            self.points_programmer.load_stage_map(s)

            return True
        else:
            return False

    def _get_calibrate_stage_label(self):
        if self._calibration_state == 'set_center':
            r = 'Locate Center'
        elif self._calibration_state == 'set_right':
            r = 'Locate Right'
        else:
            r = 'Calibrate Stage'
        return r

    def _get_program_points_label(self):
        return 'Program Points' if not self.canvas.markup else 'End Program'

    def _validate_hole(self, v):
        nv = None
        try:
            if v.strip():
                nv = int(v)

        except TypeError:
            self.warning('invalid hole {}'.format(v))

        return nv

    #    def _get_calibrated_position_entry(self):
    #        return self._calibrated_position
    #
    #    def _set_calibrated_position_entry(self, v):
    #        self._calibrated_position = v
    #        if XY_REGEX.match(v):
    #            self._move_to_calibrated_position(v)
    #        else:
    #            self.move_to_hole(v)
    def _calibrated_position_entry_changed(self):
        v = self.calibrated_position_entry
        self.goto_position(v)

    def _move_to_calibrated_position(self, pos):
        try:
            args = map(float, pos.split(','))
        except ValueError:
            self.warning('invalid calibrated position "{}". Could not convert to floats'.format(pos))
            return

        if len(args) == 2:
            x, y = args
            self.linear_move(x, y, use_calibration=True, block=False)
        else:
            self.warning('invalid calibrated position. incorrect number of arguments "{}"'.format(args))


    #    def _set_hole(self, v):
    #        if v is None:
    #            return
    #
    #        if self.canvas.calibrate:
    #            self.warning_dialog('Cannot move while calibrating')
    #            return
    #
    #        if self.canvas.markup:
    #            self.warning_dialog('Cannot move while adding/editing points')
    #            return
    #
    #        v = str(v)
    #
    #        if self.move_thread is not None:
    #            self.stage_controller.stop()
    #
    # #        if self.move_thread is None:
    #
    #        pos = self._stage_map.get_hole_pos(v)
    #        if pos is not None:
    #            self.visualizer.set_current_hole(v)
    # #            self._hole = v
    #            self.move_thread = Thread(name='stage.move_to_hole',
    #                                      target=self._move_to_hole, args=(v,))
    #            self.move_thread.start()
    #        else:
    #            err = 'Invalid hole {}'.format(v)
    #            self.warning(err)
    #            return  err

    #    def _get_hole(self):
    #        return self._hole

    def _set_point(self, v):
        if self.canvas.calibrate:
            self.warning_dialog('Cannot move while calibrating')
            return

        if self.canvas.markup:
            self.warning_dialog('Cannot move while adding/editing points')
            return

        if (self.move_thread is None or \
                not self.move_thread.isRunning()) and \
                        v is not self._point:
            pos = self.canvas.get_item('point', int(v) - 1)
            if pos is not None:
                self._point = v
                self.move_thread = Thread(target=self._move_to_point, args=(pos,))
                self.move_thread.start()
            else:
                err = 'Invalid point {}'.format(v)
                self.warning(err)
                return err

    def _get_point(self):
        return self._point

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _stop_button_fired(self):
        self._stop()

    def _back_button_fired(self):
        pos, kw = self.linear_move_history.pop(-1)
        t = Thread(target=self.stage_controller.linear_move, args=pos, kwargs=kw)
        t.start()
        self.move_thread = t

    def __stage_map_changed(self):
        self.canvas.set_map(self._stage_map)
        self.tray_calibration_manager.load_calibration(stage_map=self.stage_map)
        self.canvas.request_redraw()

    def _ejoystick_fired(self):
        self.joystick = not self.joystick
        if self.joystick:
            self.stage_controller.enable_joystick()
            self.joystick_label = 'Disable Joystick'

            self.joystick_timer = self.timer_factory(func=self._joystick_inprogress_update)
        else:
            if self.joystick_timer is not None:
                self.joystick_timer.Stop()

            self.stage_controller.disable_joystick()
            self.joystick_label = 'Enable Joystick'

    def _home_fired(self):
        """
        """
        t = Thread(
            name='stage.home',
            target=self._home)
        t.start()
        # need to store a reference to thread so it is not garbage collected
        self.move_thread = t

    def _test_fired(self):
    #        self.do_pattern('testpattern')
        self.do_pattern('pattern003')

    # ===============================================================================
    # factories
    # ===============================================================================
    def motion_configure_factory(self, **kw):
        return MotionControllerManager(motion_controller=self.stage_controller,
                                       application=self.application,
                                       **kw)

    def _stage_controller_factory(self):
        if self.stage_controller_class == 'Newport':
            from pychron.hardware.newport.newport_motion_controller import NewportMotionController

            factory = NewportMotionController
        elif self.stage_controller_class == 'Aerotech':
            from pychron.hardware.aerotech.aerotech_motion_controller import AerotechMotionController

            factory = AerotechMotionController

        m = factory(name='{}controller'.format(self.name),
                    configuration_name='stage_controller',
                    configuration_dir_name=self.configuration_dir_name,
                    parent=self)
        return m

    def _canvas_factory(self):
        """
        """
        w = 640 / 2.0 / 23.2
        h = 0.75 * w

        l = LaserTrayCanvas(stage_manager=self,
                            padding=[30, 5, 5, 30],
                            map=self._stage_map,
                            view_x_range=[-w, w],
                            view_y_range=[-h, h])

        return l

    def _canvas_editor_factory(self):
        return self.canvas_editor_klass(keyboard_focus='keyboard_focus')

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _canvas_default(self):
        return self._canvas_factory()

    def _motion_controller_manager_default(self):
        return self.motion_configure_factory()

    def _title_default(self):
        return '%s Stage Manager' % self.name[:-5].capitalize()

    def _tray_calibration_manager_default(self):
        t = TrayCalibrationManager(parent=self,
                                   canvas=self.canvas)
        return t

    def _points_programmer_default(self):
        pp = PointsProgrammer(canvas=self.canvas,
                              stage_map_klass=self.stage_map_klass,
                              stage_manager=self)
        pp.on_trait_change(self.move_to_point, 'point')
        pp.on_trait_change(self.move_polygon, 'polygon')
        pp.on_trait_change(self.move_polyline, 'line')
        return pp

    def traits_view(self):
        '''
        '''
        self.initialize_stage()

        editor = self._canvas_editor_factory()
        canvas_grp = VGroup(
            # Item('test'),
            HGroup(Item('stage_map', show_label=False,
                        editor=EnumEditor(name='object.stage_maps')),
                   Item('_stage_map',
                        show_label=False),
                   Item('back_button',
                        enabled_when='object.linear_move_history',
                        show_label=False),
                   spring),
            Item('canvas', style='custom', editor=editor,
                 show_label=False,
                 resizable=False))

        #        vg = VGroup()
        #        hooks = [h for h in dir(self) if '__group__' in h]
        #        for h in hooks:
        #            vg.content.append(getattr(self, h)())

        #        return View(HSplit(vg, canvas_group), handler=self.handler_klass)
        return View(canvas_grp,
                    #                    handler=self.handler_klass
        )

# ===============================================================================
# mass spec hacks
# ===============================================================================
#    _temp_position = None
#    def _get_temp_position(self):
#        return self._temp_position
#
#    def _set_temp_position(self, v):
#        self._temp_position = v
#
#    temp_position = property(fget=_get_temp_position,
#                           fset=_set_temp_position)


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('stage_manager')
    name = 'diode'
    s = StageManager(
        name='{}stage'.format(name),
        configuration_dir_name=name,
        # parent = DummyParent(),
        window_width=945,
        window_height=545

    )
    #    from pychron.initializer import Initializer
    #
    #    i = Initializer()
    #    i.add_initialization(dict(name = 'stage_manager',
    #                              manager = s
    #                              ))
    #    i.run()
    #    s.update_axes()
    s.load()
    s.stage_controller.bootstrap()
    s.configure_traits()
#========================EOF============================

# view groups
    # ===============================================================================
    #    def _hole__group__(self):
    #        g = Group(HGroup(Item('hole'), spring))
    #        return g
    #    def _position__group__(self):
    #        g = Group(HGroup(Item('calibrated_position_entry', label='Position',
    #                              tooltip='Enter a x,y point in reference frame space',
    #                              ), spring))

    #        g = Group(
    #                  Item('calibrated_position_entry',
    #                       show_label=False,
    #                       tooltip='Enter a positon e.g 1 for a hole, or 3,4 for X,Y'
    #                       ), label='Calibrated Position',
    #                  show_border=True)
    #        return g

    #    def _button__group__(self):
    #        '''
    #        '''
    #        vg = VGroup()
    #
    #        home = self._button_factory(*self.buttons[0])
    #        calibrate_stage = self._button_factory(*self.buttons[1])
    #
    #        vg.content.append(HGroup(calibrate_stage, home,
    #                                 Item('home_option',
    #                                      editor=EnumEditor(values=self.home_options),
    #                                      show_label=False)))
    #
    #        if len(self.buttons) > 2:
    #        # vg.content.append(self._button_group_factory(self.buttons[:2], orientation = 'h'))
    #            vg.content.append(self._button_group_factory(self.buttons[2:], orientation='h'))
    #        return vg

    #    def _axis__group__(self):
    #        '''
    #        '''
    #        return Item('stage_controller', show_label=False, style='custom')
    #
    #
    #    def _sconfig__group__(self):
    #        '''
    #        '''
    #        return Group(
    # #                     Item('pattern_manager',
    # #                          label='Pattern',
    # #                          editor=InstanceEditor(view='execute_view'),
    # #                           show_label=False, style='custom'
    # #                          ),
    #
    #                     Group(
    #                           Item('canvas', show_label=False,
    #                                 editor=InstanceEditor(view='config_view'),
    #                                 style='custom'
    #                                 ),
    #                           label='Canvas'),
    #
    # #                     Group(Item('motion_controller_manager', editor=InstanceEditor(view='configure_view'),
    # #                                 style='custom', show_label=False),
    # #                           Item('motion_profiler', style='custom', show_label=False),
    # #                           label='Motion'
    # #                           ),
    #
    # #                     Group(
    # #                            self._button_factory('program_points', 'program_points_label'),
    # #                            Item('accept_point', show_label=False),
    # #                            Item('load_points', show_label=False),
    # #                            Item('save_points', show_label=False),
    # #                            Item('clear_points', show_label=False),
    # #                            label='Points'),
    #                     Item('points_programmer',
    #                          label='Points',
    #                          show_label=False, style='custom'),
    #                     Item('tray_calibration_manager',
    #                          label='Calibration',
    #                           show_label=False, style='custom'),
    # #                     Item('pattern_manager',
    # #                          label='Pattern',
    # #                          editor=InstanceEditor(view='execute_view'),
    # #                           show_label=False, style='custom'
    # #                          ),
    #
    # #                     Item('output', show_label = False, style = 'custom'),
    #
    # #                     Item('jog_manager', show_label = False, style = 'custom',
    # #                          resizable=False
    # #                          ),
    #                     layout='tabbed'
    #                     )

