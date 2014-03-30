#===============================================================================
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
#===============================================================================

#=============enthought library imports=======================
from traits.api import Color, Property, Tuple, Float, Any, Bool, Range, on_trait_change, \
    Enum, List, Int, File, Instance
# from traitsui.api import View, Item, VGroup, HGroup, ColorEditor
from chaco.api import AbstractOverlay
from kiva import constants
from kiva.agg.agg import GraphicsContextArray
#=============standard library imports ========================
from numpy import array
from PIL import Image
# import math
#=============local library imports  ==========================
from pychron.canvas.canvas2D.map_canvas import MapCanvas

from pychron.canvas.canvas2D.scene.primitives.laser_primitives import Transect, \
    VelocityPolyLine, RasterPolygon, LaserPoint, DrillPoint
from pychron.canvas.canvas2D.crosshairs_overlay import CrosshairsOverlay
import os
from chaco.data_view import DataView


# class Point(HasTraits):
#    x=Float
#    y=Float
#    identifier=Str

# class PointOverlay(AbstractOverlay):
#    def overlay(self, component, gc, *args, **kw):
#        with gc:
#            gc.clip_to_rect(component.x, component.y, component.width, component.height)
#            for pt in self.component.points:
#                pt.render(gc)
#
# class LineOverlay(AbstractOverlay):
#    def overlay(self, component, gc, *args, **kw):
#        with gc:
#            gc.clip_to_rect(component.x, component.y, component.width, component.height)
#            for li in self.component.lines:
#                li.render(gc)
#
# class MarkupOverlay(AbstractOverlay):
#    def overlay(self, component, gc, *args, **kw):
#        with gc:
#            gc.clip_to_rect(component.x, component.y, component.width, component.height)
#            for li in self.component.markup_objects:
#                li.render(gc)
from pychron.experiment.utilities.position_regex import TRANSECT_REGEX, DRILL_REGEX


class BoundsOverlay(AbstractOverlay):
    def overlay(self, component, gc, *args, **kw):
        gc.save_state()
        (x1, y1), (x2, y2) = component.map_screen([(-25, -25), (25, 25)])
        w = abs(x1 - x2)
        h = abs(y1 - y2)
        gc.set_stroke_color((1, 0, 0))
        gc.set_line_width(3)
        gc.set_line_dash((5, 5))
        rect = [getattr(component, attr) for attr in ('x', 'y', 'width', 'height')]
        gc.clip_to_rect(*rect)

        gc.draw_rect((x1 + 1, y1, w, h), constants.STROKE)
        gc.restore_state()


DIRECTIONS = {'Left': ('x', 1), 'Right': ('x', -1),
              'Down': ('y', 1), 'Up': ('y', -1)
}


class ImageOverlay(AbstractOverlay):
    alpha = Range(0.0, 1.0, 1.0)

    _image_cache_valid = False
    _cached_image = None

    path = File

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            #             gc.clip_to_rect(0, 0, scomponent.width, self.component.height)
            gc.set_alpha(self.alpha)
            if not self._image_cache_valid:
                self._compute_cached_image()

            if self._cached_image:
                gc.draw_image(self._cached_image,
                              rect=(other_component.x, other_component.y,
                                    other_component.width, other_component.height))

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
            raise RuntimeError, "Unknown colormap depth value: %i" \
                                % data.value_depth

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


class LaserTrayCanvas(MapCanvas):
    """
    """
    markup = Bool(False)
    configuration_dir = None

    stage_position = Property(depends_on='_stage_position')
    _stage_position = Tuple(Float, Float)

    desired_position = Property(depends_on='_desired_position')
    _desired_position = Any

    bgcolor = 'mediumturquoise'

    show_axes = True
    current_position = Property(depends_on='cur_pos')
    cur_pos = Tuple(Float(0), Float(0))

    tool_state = None
    prev_x_val = 0
    prev_y_val = 0

    parent = Any

    show_desired_position = Bool(True)

    desired_position_color = Color('green')
    show_laser_position = Bool(True)

    use_zoom = False

    beam_radius = Float(0)
    crosshairs_kind = Enum('BeamRadius', 'UserRadius', 'MaskRadius')

    crosshairs_color = Color

    crosshairs_offset_color = Color('blue')

    crosshairs_radius = Range(0.0, 4.0, 1.0)
    crosshairs_offsetx = Int
    crosshairs_offsety = Int
    crosshairs_overlay = Instance(CrosshairsOverlay)

    show_bounds_rect = Bool(True)
    transects = List
    lines = List
    polygons = List

    _new_line = True
    _new_transect = True
    _new_polygon = True

    aspect_ratio = 4 / 3.

    def __init__(self, *args, **kw):
        super(LaserTrayCanvas, self).__init__(*args, **kw)
        self._add_bounds_rect()
        self._add_crosshairs()

    def add_image_underlay(self, p, alpha=1.0):
        im = ImageOverlay(path=p, alpha=alpha)
        self.overlays.append(im)

    def clear_all(self):
        self.point_count = 1
        self.lines = []
        self.transects = []
        self.polygons = []
        self.reset_markup()
        self.scene.reset_layers()

    def reset_markup(self):
        self._new_line = True
        self._new_transect = True
        self._new_polygon = True

    def point_exists(self, x, y, z, tol=1e-5):
        pt = next((pts for pts in self.get_points()
                   if abs(pts.x - x) < tol and abs(pts.y - y) < tol and abs(pts.z - z) < tol), None)

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

    def new_transect_point(self, xy=None, step=1, line_color=(1, 0, 0), point_color=(1, 0, 0), **ptargs):
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

    def new_line_point(self, xy=None, z=0, line_color=(1, 0, 0), point_color=(1, 0, 0), velocity=None, **kw):
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

        if not 'identifier' in kw:
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
            if self.parent is not None:
                p = self.parent.stage_controller
                x, y = self.map_data((x, y))

                try:
                    if between(p.xaxes_min, x, p.xaxes_max) and \
                            between(p.yaxes_min, y, p.yaxes_max):
                        return x, y
                except AttributeError:
                    pass

    def map_offset_position(self, pos):
        """
            input a x,y tuple in data space
            return the position modified by crosshairs offset
        """
        sx, sy = pos
        sx += self.crosshairs_offsetx
        sy += self.crosshairs_offsety

        return self.map_data((sx, sy))

    def get_offset_stage_position(self):
        pos = self.get_stage_screen_position()
        return self.map_offset_position(pos)

    def get_offset_stage_screen_position(self):
        sx, sy = self.get_stage_screen_position()
        return sx + self.crosshairs_offsetx, sy + self.crosshairs_offsety

    def get_stage_screen_position(self):
        return self.map_screen([self._stage_position])[0]

    def get_stage_position(self):
        return self._stage_position

        #return (self._stage_position[0]-self.crosshairs_offsetx,
        #self._stage_position[1] - self.crosshairs_offsety)

    def set_stage_position(self, x, y):
        """
        """
        if x is not None and y is not None:
            self._stage_position = (x, y)
            self.invalidate_and_redraw()

    def clear_desired_position(self):
        pass

    #    def clear_desired_position(self):
    #        self._desired_position = None
    #        self.request_redraw()

    def set_desired_position(self, x, y):
        """
        """
        self._desired_position = (x, y)
        self.request_redraw()

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

            d = val - getattr(self, pname)
            setattr(self, pname, val)

            nmi = vmi + d
            nma = vma + d
        else:
            delta /= 2.0
            nmi = val - delta
            nma = val + delta

        self.set_mapper_limits(mapper, (nmi, nma))

    #===============================================================================
    # interactor
    #===============================================================================
    def normal_left_down(self, event):
        """
        """
        #        if self.calibrate or self.markup:
        #            super(LaserTrayCanvas, self).normal_left_down(event)
        #
        #        else:
        x = event.x - self.crosshairs_offsetx
        y = event.y - self.crosshairs_offsety

        pos = self.valid_position(x, y)
        if pos:
            if not self._frozen:
                self.parent.linear_move(*pos, use_calibration=False)
            event.handled = True

            #    def normal_mouse_wheel(self, event):
            #        enable_mouse_wheel_zoom = False
            #        if enable_mouse_wheel_zoom:
            #            inc = event.mouse_wheel
            # #            self.parent.parent.laser_controller.set_zoom(inc, relative=True)
            #            self.parent.parent.laser_controller.set_motor('zoom', inc, relative=True)
            # #            self.parent.parent.logic_board.set_zoom(inc, relative=True)
            #            event.handled = True

    def normal_key_pressed(self, event):
        c = event.character
        if not self._frozen:
            if c in ['Left', 'Right', 'Up', 'Down']:
                ax_key, direction = DIRECTIONS[c]
                direction = self._calc_relative_move_direction(c, direction)
                self.parent.relative_move(ax_key, direction)
                event.handled = True
            elif c in ('a', 'A'):
                self.parent.accept_point()

    def key_released(self, char):
        """
            called from outside by StageCompnentEditor
        """
        if not self._frozen:
            if char in ('left', 'right'):
                self.parent.stop(ax_key='x', verbose=False)
                self.parent.update_axes()
            elif char in ('up', 'down'):
                self.parent.stop(ax_key='y', verbose=False)
                self.parent.update_axes()

    def normal_mouse_move(self, event):
        """
        """
        self.cur_pos = (event.x, event.y)
        #        if self.calibrate or self.markup:
        #            super(LaserTrayCanvas, self).normal_mouse_move(event)
        #
        #            #both the markup and map canvas can handle this event
        #            MarkupCanvas.normal_mouse_move(self, event)
        #            if not event.handled:
        #                MapCanvas.normal_mouse_move(self, event)
        #        else:

        if self.valid_position(event.x, event.y):
            event.window.set_pointer(self.cross_pointer)
        else:
            event.window.set_pointer(self.normal_pointer)

        event.handled = True
        self.request_redraw()

    def normal_mouse_enter(self, event):
        """
        """
        event.window.set_pointer(self.cross_pointer)
        event.handled = True

    def normal_mouse_leave(self, event):
        """
        """
        event.window.set_pointer(self.normal_pointer)
        self.request_redraw()
        event.handled = True

    #===============================================================================
    # private
    #===============================================================================
    def _calc_relative_move_direction(self, char, direction):
        return direction

    def _add_bounds_rect(self):
        if self.show_bounds_rect:
            self.overlays.append(BoundsOverlay(component=self))

    def _add_crosshairs(self):
        ch = CrosshairsOverlay(component=self)
        #self.overlays.append(ch)
        self.crosshairs_overlay = ch

    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('''show_laser_position, show_desired_position,
                         desired_position_color,
                         crosshairs_+
                         ''')
    def change_indicator_visibility(self, name, new):
        self.request_redraw()

    def _show_bounds_rect_changed(self):
        bo = next((o for o in self.overlays if isinstance(o, BoundsOverlay)), None)
        if bo is None:
            self._add_bounds_rect()
        elif not self.show_bounds_rect:
            self.overlays.remove(bo)

        self.request_redraw()

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_crosshairs_color(self):
        return self._crosshairs_color

    def _get_current_position(self):

        md = self.map_data(self.cur_pos)
        return self.cur_pos[0], md[0], self.cur_pos[1], md[1]

    def _get_stage_position(self):
        """
        """

        return self.map_screen([self._stage_position])[0]

    def _get_desired_position(self):
        """
        """

        if not self._desired_position is None:
            x, y = self.map_screen([self._desired_position])[0]
            return x, y

    #===============================================================================
    # defaults
    #===============================================================================
    def _scene_default(self):
        from pychron.canvas.canvas2D.scene.laser_mine_scene import LaserMineScene

        s = LaserMineScene(canvas=self)
        return s

    #===============================================================================
    # draw
    #===============================================================================
    def draw(self, gc, *args, **kw):
        """

        """
        with gc:
            DataView.draw(self, gc, *args, **kw)
            gc.clip_to_rect(self.x, self.y,
                            self.width, self.height)
            self._draw_hook(gc, *args, **kw)

            ch = self.crosshairs_overlay
            if ch:
                ch.overlay(self, gc, *args, **kw)

                #for o in self.crosshairs_overlays:
                #if o.visible:
                #o.overlay(self, gc, *args, **kw)
                #========================EOF====================================================
                #    def _set_transect_points(self, tran, step, line_color=(1, 0, 0), point_color=(1, 0, 0), **ptargs):
                #        for pi in tran.step_points:
                #            self.remove_point(pi)
                #
                #        tran.step_points = []
                #
                #        for li in tran.lines:
                #            p1 = li.start_point
                #            p2 = li.end_point
                # #            p1 = tran.start_point
                # #            p2 = tran.end_point
                #
                #            x, y = p1.x, p1.y
                # #            p = self.new_point((x, y), **ptargs)
                # #            tran.step_points.append(p)
                #            tol = step / 3.
                #            while 1:
                #                x, y = calc_point_along_line(x, y, p2.x, p2.y, step)
                #                ptargs['use_border'] = False
                #                if abs(p2.x - x) < tol and abs(p2.y - y) < tol:
                # #                    ptargs['use_border'] = True
                #                    p = self.new_point((p2.x, p2.y), **ptargs)
                #                    tran.step_points.append(p)
                #                    break
                #                else:
                # #                    ptargs['use_border'] = False
                #                    p = self.new_point((x, y),
                #                                   line_color=line_color, point_color=point_color,
                #                                   **ptargs)
                #                    tran.step_points.append(p)
                #
                #    #            line.add_point(*xy,
                #    #                           line_color=line_color,
                #    #                           point_color=point_color)
                #    def remove_point_overlay(self):
                #        for o in self.overlays[:]:
                #            if isinstance(o, PointOverlay):
                #                self.overlays.remove(o)
                #
                #    def remove_line_overlay(self):
                #        for o in self.overlays[:]:
                #            if isinstance(o, LineOverlay):
                #                self.overlays.remove(o)
                #    def remove_markup_overlay(self):
                #        for o in self.overlays[:]:
                #            if isinstance(o, MarkupOverlay):
                #                self.overlays.remove(o)

                #    def add_point_overlay(self):
                #        po = PointOverlay(component=self)
                #        self.overlays.append(po)

                #    def add_line_overlay(self):
                #        po = LineOverlay(component=self)
                #        self.overlays.append(po)

                #    def add_markup_overlay(self):
                #        mo = MarkupOverlay(component=self)
                #        self.overlays.append(mo)
                #    def _draw_hook(self, gc, *args, **kw):
                #        '''
                #        '''
                #        if self.show_desired_position and self.desired_position is not None:
                #            # draw the place you want the laser to be
                #            self._draw_crosshairs(gc, self.desired_position, color=self.desired_position_color, kind=2)
                #
                #        if self.show_laser_position:
                #            # draw where the laser is
                #            # laser indicator is always the center of the screen
                #            pos = (self.x + (self.x2 - self.x) / 2.0  , self.y + (self.y2 - self.y) / 2.0)
                #
                # #            #add the offset
                # #            if self.crosshairs_offset is not (0, 0):
                # #                pos_off = pos[0] + self.crosshairs_offset[0], pos[1] + self.crosshairs_offset[1]
                # #                self._draw_crosshairs(gc, pos_off, color=self.crosshairs_offset_color, kind=5)
                #
                #
                # #            self._draw_crosshairs(gc, pos, color = colors1f[self.crosshairs_color])
                #            self._draw_crosshairs(gc, pos, color=self.crosshairs_color)
                #
                #        super(LaserTrayCanvas, self)._draw_hook(gc, *args, **kw)

                #    def _draw_crosshairs(self, gc, xy, color=(1, 0, 0), kind=None):
                #        '''
                #        '''
                #
                #        gc.save_state()
                #        gc.set_stroke_color(color)
                #        mx, my = xy
                #        mx += 1
                #        my += 1
                #
                #        if self.crosshairs_kind == 'BeamRadius':
                #            r = self.beam_radius
                #        elif self.crosshairs_kind == 'MaskRadius':
                #            r = 0
                #            if self.parent:
                #                mask = self.parent.parent.get_motor('mask')
                #                if mask is not None:
                #                    r = mask.get_discrete_value()
                #        else:
                #            r = self.crosshairs_radius
                #
                #        if r:
                #            r = self._get_wh(r, 0)[0]
                #            gc.arc(mx, my, r, 0, 360)
                #
                #            gc.move_to(self.x, my)
                #            gc.line_to(mx - r, my)
                #
                #            gc.move_to(mx + r, my)
                #            gc.line_to(self.x2, my)
                #
                #            gc.move_to(mx, self.y)
                #            gc.line_to(mx, my - r)
                #            gc.move_to(mx, my + r)
                #            gc.line_to(mx, self.y2)
                #            gc.stroke_path()
                #
                #        b = 4
                #        gc.move_to(mx - b, my)
                #        gc.line_to(mx + b, my)
                #        gc.move_to(mx, my - b)
                #        gc.line_to(mx, my + b)
                #        gc.stroke_path()
                #
                #        gc.restore_state()
                #===============================================================================
                #
                #           1 |
                #             |
                #        0---- m,m  -----2
                #             |
                #             |3
                #        kind 0 none
                #        kind 1 with circle
                #        kind 2 with out circle
                #        kind 3 +
                #===============================================================================

                #        if kind is None:
                #            kind = self.crosshairs_kind
                #
                #        beam_radius = 0
                #        if kind in [1, 5]:
                # #            args = self.map_screen([(0, 0), (0, self.beam_radius + 0.5),
                # #                                    (0, 0), (self.beam_radius + 0.5, 0)
                # #                                    ])
                # #            beam_radius = abs(args[0][1] - args[1][1])
                #            beam_radius = self._get_wh(self.beam_radius, 0)[0]
                #
                #        elif kind == 2:
                #            beam_radius = 10
                #        elif kind == 3:
                #            beam_radius = 0
                #        elif kind == 4:
                #            beam_radius = self._get_wh(self.crosshairs_radius, 0)[0]
                #        else:
                #            return
                #
                #        gc.set_stroke_color(color)
                #
                #        if kind is not 5:
                #            p00 = self.x, my
                #            p01 = mx - beam_radius, my
                #
                #            p10 = mx, my + beam_radius
                #            p11 = mx, self.y2
                #
                #            p20 = mx + beam_radius, my
                #            p21 = self.x2, my
                #
                #            p30 = mx, my - beam_radius
                #            p31 = mx, self.y
                #
                #            points = [(p00, p01), (p10, p11),
                #                      (p20, p21), (p30, p31)]
                #
                #            for p1, p2 in points:
                #
                #                gc.begin_path()
                #                gc.move_to(*p1)
                #                gc.line_to(*p2)
                #                gc.close_path()
                #                gc.draw_path()
                # #                gc.stroke_path()
                #
                #        if kind in [1, 4, 5]:
                #            gc.set_fill_color((0, 0, 0, 0))
                #            if kind == 5:
                #                step = 20
                #                for i in range(0, 360, step):
                #                    gc.arc(mx, my, beam_radius, math.radians(i),
                #                                           math.radians(i + step / 2.0))
                #                    gc.draw_path()
                #
                #            else:
                #                gc.arc(mx, my, beam_radius, 0, math.radians(360))
                #            gc.draw_path()
                #
                #        gc.restore_state()


                #========================EOF============================
                #    def clear_points(self):
                #        popkeys = []
                #        self.point_counter = 0
                #        for k, v in self.markupcontainer.iteritems():
                #            if isinstance(v, PointIndicator):
                #                popkeys.append(k)
                #        for p in popkeys:
                #            self.markupcontainer.pop(p)
                #        self.request_redraw()
                #
                #    def load_points_file(self, p):
                #        self.point_counter = 0
                #        with open(p, 'r') as f:
                #            for line in f:
                #                identifier, x, y = line.split(',')
                #                pt = self.point_exists(float(x), float(y))
                #                if pt is not None:
                #                    self.markupcontainer.pop(pt.identifier)
                #
                #                self.markupcontainer[identifier] = PointIndicator(float(x), float(y), identifier=identifier, canvas=self)
                #                self.point_counter += 1
                #
                #        self.request_redraw()
                #
                #    def get_points(self):
                #        pts=[]
                #        for _k, v in self.markupcontainer.iteritems():
                #            if isinstance(v, PointIndicator):
                #
                #                pts.append((v.identifier, v.x, v.y))
                #
                # #                lines.append(','.join(map(str, )))
                #        pts=sorted(pts, key=lambda x: x[0])
                #        return pts
                #    def save_points(self, p):
                #        lines = []
                #        for _k, v in self.markupcontainer.iteritems():
                #            if isinstance(v, PointIndicator):
                #                lines.append(','.join(map(str, (v.identifier, v.x, v.y))))
                #
                #        with open(p, 'w') as f:
                #            f.write('\n'.join(lines))
                #    def config_view(self):
                #        v = View(
                #                VGroup(
                #                       Item('show_bounds_rect'),
                # #                       Item('render_map'),
                #                       Item('show_grids'),
                #                       HGroup(Item('show_laser_position'),
                #                              Item('crosshairs_color',
                #                                   editor=ColorEditor(),
                #                                   springy=True, show_label=False)
                #                              ),
                #                       Item('crosshairs_kind'),
                #                       Item('crosshairs_radius'),
                #                       HGroup(
                #                              Item('crosshairs_offsetx', label='Offset'),
                #                              Item('crosshairs_offsety', show_label=False)
                #                              ),
                #                       Item('crosshairs_offset_color'),
                #                       HGroup(Item('show_desired_position'),
                #                              Item('desired_position_color', springy=True, show_label=False)),
                #                       )
                #            )
                #        return v