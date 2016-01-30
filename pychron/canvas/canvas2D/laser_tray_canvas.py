# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import Color, Float, Any, Bool, Range, on_trait_change, \
    Enum, List, File
# from traitsui.api import View, Item, VGroup, HGroup, ColorEditor
from chaco.api import AbstractOverlay
from kiva import constants
from kiva.agg.agg import GraphicsContextArray
# =============standard library imports ========================
from numpy import array
from PIL import Image
# import math
# =============local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.laser_primitives import Transect, \
    VelocityPolyLine, RasterPolygon, LaserPoint, DrillPoint
from pychron.canvas.canvas2D.crosshairs_overlay import CrosshairsOverlay
import os
from pychron.canvas.canvas2D.stage_canvas import StageCanvas, DIRECTIONS
from pychron.experiment.utilities.position_regex import TRANSECT_REGEX, \
    DRILL_REGEX


class BoundsOverlay(AbstractOverlay):
    def overlay(self, component, gc, *args, **kw):
        with gc:
            (x1, y1), (x2, y2) = component.map_screen([(-25, -25), (25, 25)])
            w = abs(x1 - x2)
            h = abs(y1 - y2)
            gc.set_stroke_color((1, 0, 0))
            gc.set_line_width(3)
            gc.set_line_dash((5, 5))
            rect = [getattr(component, attr) for attr in
                    ('x', 'y', 'width', 'height')]
            gc.clip_to_rect(*rect)

            gc.draw_rect((x1 + 1, y1, w, h), constants.STROKE)


class ImageOverlay(AbstractOverlay):
    alpha = Range(0.0, 1.0, 1.0)

    _image_cache_valid = False
    _cached_image = None

    path = File

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.set_alpha(self.alpha)
            if not self._image_cache_valid:
                self._compute_cached_image()

            if self._cached_image:
                gc.draw_image(self._cached_image,
                              rect=(other_component.x, other_component.y,
                                    other_component.width,
                                    other_component.height))

    def _compute_cached_image(self):
        pic = Image.open(self.path)
        data = array(pic)
        if not data.flags['C_CONTIGUOUS']:
            data = data.copy()

        if data.shape[2] == 3:
            kiva_depth = "rgb24"
        elif data.shape[2] == 4:
            kiva_depth = "rgba32"
        else:
            raise RuntimeError(
                    "Unknown colormap depth value: %i".format(data.value_depth))

        self._cached_image = GraphicsContextArray(data, pix_format=kiva_depth)
        self._image_cache_valid = True

    def _path_changed(self):
        if self.path:
            self.name = os.path.basename(self.path)
            self.dirname = os.path.dirname(self.path)

        self._image_cache_valid = False
        self.request_redraw()

    def _alpha_changed(self):
        self.request_redraw()


class LaserTrayCanvas(StageCanvas):
    """
    """
    markup = Bool(False)
    configuration_dir = None

    bgcolor = 'mediumturquoise'

    # show_axes = True
    tool_state = None

    stage_manager = Any

    show_laser_position = Bool(True)

    use_zoom = False

    beam_radius = Float(0)
    crosshairs_kind = Enum('BeamRadius', 'UserRadius', 'MaskRadius')
    crosshairs_offset_color = Color('blue')

    crosshairs_radius = Range(0.0, 4.0, 1.0)
    crosshairs_offsetx = Float
    crosshairs_offsety = Float

    show_bounds_rect = Bool(True)
    transects = List
    lines = List
    polygons = List

    _new_line = True
    _new_transect = True
    _new_polygon = True

    aspect_ratio = 4 / 3.

    def _show_axes_default(self):
        return True

    def __init__(self, *args, **kw):
        super(LaserTrayCanvas, self).__init__(*args, **kw)
        self._add_bounds_rect()
        self._add_crosshairs()
        self.border_visible = False

    def add_image_underlay(self, p, alpha=1.0):
        im = ImageOverlay(path=p, alpha=alpha)
        self.overlays.append(im)

    def clear_all(self):
        self.point_count = 1
        self.lines = []
        self.transects = []
        self.polygons = []
        self.reset_markup()
        if self.scene:
            self.scene.reset_layers()

    def reset_markup(self):
        self._new_line = True
        self._new_transect = True
        self._new_polygon = True

    def point_exists(self, x, y, z, tol=1e-5):
        pt = next((pts for pts in self.get_points()
                   if abs(pts.x - x) < tol and abs(pts.y - y) < tol and abs(
                pts.z - z) < tol), None)

        return True if pt else False

    def set_transect_step(self, step):
        transect = self.transects[-1]

        transect.step = step
        self.request_redraw()

    def new_polygon_point(self, xy=None,
                          ptargs=None,
                          identifier=None,
                          line_color=(1, 0, 0),
                          point_color=(1, 0, 0),
                          **kw):
        if ptargs is None:
            ptargs = dict()

        if xy is None:
            xy = self._stage_position

        if identifier is None:
            identifier = str(len(self.polygons) + 1)

        if self._new_polygon:
            self._new_polygon = False
            poly = RasterPolygon([xy],
                                 identifier=identifier,
                                 default_color=point_color,
                                 ptargs=ptargs,
                                 **kw)
            self.polygons.append(poly)
            self.scene.add_item(poly)
        else:
            poly = self.polygons[-1]
            poly.add_point(xy, default_color=point_color, **ptargs)

    def new_transect_point(self, xy=None, step=1, line_color=(1, 0, 0),
                           point_color=(1, 0, 0), **ptargs):
        if xy is None:
            xy = self._stage_position

        if self._new_transect:
            self._new_transect = False

            transect = Transect(xy[0], xy[1],
                                identifier=str(len(self.transects) + 1),
                                canvas=self,
                                default_color=point_color,
                                step=step,
                                **ptargs)
            self.scene.add_item(transect)
            self.transects.append(transect)
        else:
            tran = self.transects[-1]

            tran.add_point(xy[0], xy[1], **ptargs)
            tran.set_step_points(**ptargs)

    def new_line_point(self, xy=None, z=0, line_color=(1, 0, 0),
                       point_color=(1, 0, 0), velocity=None, **kw):
        if xy is None:
            xy = self._stage_position

        if self._new_line:
            kw['identifier'] = str(len(self.lines) + 1)

            line = VelocityPolyLine(*xy, z=z,
                                    default_color=point_color,
                                    **kw)
            self._new_line = False
            self.scene.add_item(line)
            self.lines.append(line)
        else:
            line = self.lines[-1]
            line.velocity_segments.append(velocity)
            line.add_point(*xy,
                           z=z,
                           line_color=line_color,
                           point_color=point_color)

    def remove_item(self, name):
        self.scene.remove_item(name)

    def pop_point(self, idx):
        if idx == -1:
            self.point_count -= 1
        self.scene.pop_item(idx, klass=LaserPoint)

    def new_point(self, xy=None, redraw=True, **kw):

        if xy is None:
            xy = self._stage_position

        if 'identifier' not in kw:
            kw['identifier'] = str(self.point_count)

        p = LaserPoint(*xy, **kw)
        self.point_count += 1

        self.scene.add_item(p)
        if redraw:
            self.request_redraw()
        return p

    def get_transects(self):
        return self.scene.get_items(Transect)

    def get_lines(self):
        return self.scene.get_items(VelocityPolyLine)

    def get_points(self):
        return self.scene.get_items(LaserPoint)

    def get_polygons(self):
        return self.scene.get_items(RasterPolygon)

    def get_line(self, v):
        return self.scene.get_item(v, klass=VelocityPolyLine)

    def get_transect(self, v):
        return self.scene.get_item(v, klass=Transect)

    def get_polygon(self, v):
        return self.scene.get_item(v, klass=RasterPolygon)

    def get_drill(self, v):
        return self.scene.get_item(v, klass=DrillPoint)

    def get_point(self, v):
        if TRANSECT_REGEX[0].match(v):
            return self.get_transect_point(v)
        elif DRILL_REGEX.match(v):
            return self.get_drill_point(v)
        else:
            # v= p2 e.g. identifier is only 2
            if v.startswith('p'):
                v = v[1:]

            return self.scene.get_item(v, klass=LaserPoint)

    def get_transect_point(self, v):
        t, p = v[1:].split('-')
        tran = self.get_transect(t)
        if tran:
            return tran.get_point(int(p))

    def get_drill_point(self, v):
        drill = self.get_drill(v)
        return drill

    def valid_position(self, x, y):
        """
        """
        between = lambda mi, v, ma: mi < v <= ma

        if between(self.x, x, self.x2) and between(self.y, y, self.y2):
            if self.stage_manager is not None:
                p = self.stage_manager.stage_controller
                x, y = self.map_data((x, y))
                try:
                    if between(p.xaxes_min, x, p.xaxes_max) and \
                            between(p.yaxes_min, y, p.yaxes_max):
                        return x, y
                except AttributeError, e:
                    print e

    def map_offset_position(self, pos):
        """
            input a x,y tuple in screen space
            return the position modified by crosshairs offset
        """
        sx, sy = self.map_data(pos)
        return sx + self.crosshairs_offsetx, sy + self.crosshairs_offsety

    def get_screen_offset(self):
        (cx, cy), (ox, oy) = self.map_screen([(0, 0),
                                              (self.crosshairs_offsetx,
                                               self.crosshairs_offsety)])
        return ox - cx, oy - cy

    def get_offset_stage_position(self):
        pos = self.get_stage_screen_position()
        return self.map_offset_position(pos)

    def get_offset_stage_screen_position(self):
        sx, sy = self.get_stage_screen_position()
        return sx, sy

    def adjust_limits(self, mapper, val, delta=None):
        """
        """
        if val is None:
            return

        if delta is None:

            vrange = getattr(self, '{}_mapper'.format(mapper)).range

            vmi = vrange.low
            vma = vrange.high
            pname = 'prev_{}_val'.format(mapper)

            try:
                pv = getattr(self, pname)
            except AttributeError:
                pv = 0

            d = val - pv
            setattr(self, pname, val)

            nmi = vmi + d
            nma = vma + d
        else:
            delta /= 2.0
            nmi = val - delta
            nma = val + delta

        self.set_mapper_limits(mapper, (nmi, nma))

    # ===============================================================================
    # interactor
    # ===============================================================================
    def normal_left_down(self, event):
        """
        """

        ox, oy = self.get_screen_offset()
        x, y = event.x - ox, event.y - oy

        pos = self.valid_position(x, y)

        if pos:
            self.stage_manager.linear_move(*pos,
                                           check_moving=True,
                                           use_calibration=False)
            event.handled = True

    def normal_key_pressed(self, event):
        c = event.character
        if c in ('Left', 'Right', 'Up', 'Down'):
            ax_key, direction = DIRECTIONS[c]
            direction = self._calc_relative_move_direction(c, direction)
            distance = 5 if event.shift_down else 1
            self.stage_manager.relative_move(ax_key, direction, distance)
            event.handled = True
        elif c in ('a', 'A'):
            self.stage_manager.accept_point()

    def key_released(self, char):
        """
            called from outside by StageCompnentEditor
        """

        # if char in ('left', 'right'):
        #     # self.stage_manager.stop(ax_key='x', update=True, verbose=False)
        #     self.stage_manager.update_axes()
        # elif char in ('up', 'down'):
        #     self.stage_manager.stop(ax_key='y', verbose=False)
        #     # self.stage_manager.update_axes()
        sc = self.stage_manager.stage_controller
        sc.add_consumable((sc.update_axes, tuple()))

    # ===============================================================================
    # private
    # ===============================================================================
    def _calc_relative_move_direction(self, char, direction):
        return direction

    def _add_bounds_rect(self):
        if self.show_bounds_rect:
            self.overlays.append(BoundsOverlay(component=self))

    def _add_crosshairs(self):
        ch = CrosshairsOverlay(component=self,
                               constrain='')
        self.crosshairs_overlay = ch
        self.overlays.append(ch)

    # ===============================================================================
    # handlers
    # ===============================================================================
    @on_trait_change('''show_laser_position, show_desired_position,
                         desired_position_color,
                         crosshairs_+''')
    def change_indicator_visibility(self, name, new):
        self.request_redraw()

    def _show_bounds_rect_changed(self):
        bo = next((o for o in self.overlays if isinstance(o, BoundsOverlay)),
                  None)
        if bo is None:
            self._add_bounds_rect()
        elif not self.show_bounds_rect:
            self.overlays.remove(bo)

        self.request_redraw()

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_crosshairs_color(self):
        return self._crosshairs_color

# ========================EOF====================================================
#    def normal_mouse_wheel(self, event):
#        enable_mouse_wheel_zoom = False
#        if enable_mouse_wheel_zoom:
#            inc = event.mouse_wheel
# #            self.parent.parent.laser_controller.set_zoom(inc, relative=True)
#            self.parent.parent.laser_controller.set_motor('zoom', inc, relative=True)
# #            self.parent.parent.logic_board.set_zoom(inc, relative=True)
#            event.handled = True
