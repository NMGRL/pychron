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
from traits.api import Color, Property, Tuple, Float, Any, Bool
# from traitsui.api import View, Item, VGroup, HGroup, ColorEditor
# =============standard library imports ========================
# import math
# =============local library imports  ==========================
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas

DIRECTIONS = {'Left': ('x', -1), 'Right': ('x', 1),
              'Down': ('y', -1), 'Up': ('y', 1)}


class FurnaceCanvas(SceneCanvas):
    """
    """

    stage_position = Property(depends_on='_stage_position')
    _stage_position = Tuple(Float, Float)

    desired_position = Property(depends_on='_desired_position')
    _desired_position = Any

    bgcolor = 'mediumturquoise'

    current_position = Property(depends_on='cur_pos')
    cur_pos = Tuple(Float(0), Float(0))

    dumper = Any

    show_desired_position = Bool(True)

    desired_position_color = Color('green')

    use_zoom = False

    aspect_ratio = 3.

    def __init__(self, *args, **kw):
        super(FurnaceCanvas, self).__init__(*args, **kw)
        self.border_visible = False
        self.show_axes = False
        self.view_y_range = (-5, 5)
        self.view_x_range = (0, 50)

    def clear_all(self):
        self.scene.reset_layers()

    def valid_position(self, x, y):
        """
        """
        between = lambda mi, v, ma: mi < v <= ma
        return between(self.x, x, self.x2) and between(self.y, y, self.y2)

    #         if self.stage_manager is not None:
    #             p = self.stage_manager.stage_controller
    #
    #             x, y = self.map_data((x, y))
    #             try:
    #                 if between(p.xaxes_min, x, p.xaxes_max) and \
    #                         between(p.yaxes_min, y, p.yaxes_max):
    #                     return x, y
    #             except AttributeError, e:
    #                 print e

    def get_stage_screen_position(self):
        return self.map_screen([self._stage_position])[0]

    def get_stage_position(self):
        return self._stage_position

    def set_stage_position(self, x, y):
        """
        """
        if x is not None and y is not None:
            self._stage_position = (x, y)
            self.invalidate_and_redraw()

    def clear_desired_position(self):
        self._desired_position = None
        self.request_redraw()

    def set_desired_position(self, x, y):
        """
        """
        self._desired_position = (x, y)
        self.request_redraw()

    # ===============================================================================
    # interactor
    # ===============================================================================
    def normal_left_down(self, event):
        """
        """
        x = event.x
        y = event.y

        if self.valid_position(x, y):
            x, y = self.map_data((x, y))

            self.dumper.linear_move(x, check_moving=True, use_calibration=False)
            event.handled = True

    def normal_key_pressed(self, event):
        c = event.character
        if c in ('Left', 'Right'):
            ax_key, direction = DIRECTIONS[c]
            # direction = self._calc_relative_move_direction(c, direction)
            distance = 5 if event.shift_down else 1
            self.dumper.relative_move(ax_key, direction, distance)
            event.handled = True

    def key_released(self, char):
        """
            called from outside by StageCompnentEditor
        """
        self.dumper.update_position()

    def normal_mouse_move(self, event):
        """
        """
        self.cur_pos = (event.x, event.y)

        if self.valid_position(event.x, event.y):
            event.window.set_pointer(self.cross_pointer)
        else:
            event.window.set_pointer(self.normal_pointer)

        event.handled = True
        # self.request_redraw()

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

    # ===============================================================================
    # private
    # ===============================================================================

    # ===============================================================================
    # handlers
    # ===============================================================================
    # ===============================================================================
    # property get/set
    # ===============================================================================
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

        if self._desired_position is not None:
            x, y = self.map_screen([self._desired_position])[0]
            return x, y

            # ===============================================================================
            # defaults
            # ===============================================================================
            # def _scene_default(self):
        # s = FurnaceScene(canvas=self)
        # return s

        # ===============================================================================
        # draw
        # ===============================================================================
        # def draw(self, *args, **kw):
        # super(LaserTrayCanvas, self).draw(*args, **kw)


        # def draw(self, gc, *args, **kw):
        # """
        #
        #     """
        #     with gc:
        #         DataView.draw(self, gc, *args, **kw)
        #         gc.clip_to_rect(self.x, self.y,
        #                         self.width, self.height)
        #         self._draw_hook(gc, *args, **kw)
        #
        #         ch = self.crosshairs_overlay
        #         if ch:
        #             ch.overlay(self, gc, *args, **kw)

        # for o in self.crosshairs_overlays:
        # if o.visible:
        # o.overlay(self, gc, *args, **kw)
        # ========================EOF====================================================
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

        # def add_point_overlay(self):
        #        po = PointOverlay(component=self)
        #        self.overlays.append(po)

        #    def add_line_overlay(self):
        # po = LineOverlay(component=self)
        #        self.overlays.append(po)

        #    def add_markup_overlay(self):
        # mo = MarkupOverlay(component=self)
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
        # '''
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
        # ===============================================================================
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
        # ===============================================================================

        #        if kind is None:
        # kind = self.crosshairs_kind
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


        # ========================EOF============================
        # def clear_points(self):
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
