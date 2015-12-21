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
import math

from enable.abstract_overlay import AbstractOverlay
from traits.api import Any, Button, Enum, Float, Int, Color, \
    Bool, Range, Instance, on_trait_change, List
from traitsui.api import View, Item, VGroup, HGroup, UItem, VSplit

from pychron.loggable import Loggable


# ============= standard library imports ========================
# ============= local library imports  ==========================

class BaseMaker(Loggable):
    canvas = Any
    stage_manager = Any

    clear = Button
    #    clear_mode = Enum('all', 'all lines', 'all points', 'current line',
    #                    'current point', 'last point'
    #                    )
    clear_mode = Enum('all', 'current point')
    accept_point = Button

    point_color = Color('blue')

    use_simple_render = Bool(False)
    spot_color = Color('yellow')
    spot_size = Int(8)

    def initialize(self):
        pass

    def deinitialize(self):
        pass

    def save(self):
        d = dict()

        pts = [dict(identifier=pi.identifier,
                    z=float(pi.z),
                    mask=pi.mask, attenuator=pi.attenuator,
                    xy=[float(pi.x), float(pi.y)],
                    calibrated_xy=[float(pi.calibrated_x), float(pi.calibrated_y)],
                    offset_x=float(pi.offset_x),
                    offset_y=float(pi.offset_y),
                    ) for pi in self.canvas.get_points()]

        lines = []
        for li in self.canvas.get_lines():
            segments = []
            for i, pi in enumerate(li.points):
                v = li.velocity_segments[i / 2]
                segments.append(dict(xy=[float(pi.x), float(pi.y)],
                                     z=float(pi.z),
                                     mask=pi.mask,
                                     attenuator=pi.attenuator,
                                     velocity=v))
            lines.append(segments)

        d['points'] = pts
        d['lines'] = lines
        sd = self._save()
        if sd:
            d.update(sd)
        return d

    def _save(self):
        pass

    def _accept_point(self, ptargs):
        pass

    def clear_all_hook(self):
        pass

    def _clear_fired(self):
        cm = self.clear_mode
        if cm == 'all':
            self.canvas.clear_all()
            self.clear_all_hook()
        elif cm == 'current point':
            self.canvas.pop_point(-1)

        # elif cm == 'current point':
        #            self.canvas.points.pop(-1)

        #        if cm.startswith('current'):
        #            if cm == 'current line':
        #                self.canvas.lines.pop(-1)
        #            else:
        #                self.canvas.points.pop(-1)
        #        elif cm.startswith('all'):
        #            if cm == 'all':
        #                self.canvas.clear_all()
        #            elif cm == 'all lines':
        #                self.canvas.lines = []
        #            else:
        #                self.canvas.points = []
        #        else:
        #            line = self.canvas.lines[-1]
        #            if len(line.points):
        #                if self.mode == 'line':
        #                    line.points.pop(-1)
        #                    if line.lines:
        #                        line.lines.pop(-1)
        #                        line.velocity_segments.pop(-1)
        #                else:
        #                    self.canvas.points.pop(-1)

        self.canvas.request_redraw()

    def _accept_point_fired(self):
        radius = 0.05  # mm or 50 um

        sm = self.stage_manager
        lm = sm.parent
        mask = lm.get_motor('mask')
        attenuator = lm.get_motor('attenuator')
        mask_value, attenuator_value = None, None
        if mask:
            radius = mask.get_discrete_value()
            if not radius:
                radius = 0.05
            mask_value = mask.data_position

        if attenuator:
            attenuator_value = attenuator.data_position
            # x, y = self.canvas.get_offset_stage_position()
        x, y = self.canvas.get_stage_position()
        cx, cy = sm.get_uncalibrated_xy((x, y))

        x, y = map(float, (x, y))
        cx, cy = map(float, (cx, cy))

        x, y = map('{:0.3f}'.format, (x, y))
        cx, cy = map('{:0.3f}'.format, (cx, cy))

        x, y = map(float, (x, y))
        cx, cy = map(float, (cx, cy))
        z = sm.get_z()

        ox, oy = self.canvas.get_screen_offset()
        ptargs = dict(xy=(x, y),
                      radius=radius,
                      z=z,
                      calibrated_x=cx,
                      calibrated_y=cy,
                      spot_color=self.spot_color,
                      spot_size=self.spot_size,
                      use_simple_render=self.use_simple_render,
                      offset_x=ox,
                      offset_y=oy,
                      # offset_x=self.canvas.crosshairs_offsetx,
                      # offset_y=self.canvas.crosshairs_offsety,
                      #                      mask=mask_value,
                      #                      attenuator=attenuator_value,
                      vline_length=0.1, hline_length=0.1)
        if mask_value is not None:
            ptargs['mask'] = mask_value
        if attenuator_value is not None:
            ptargs['attenuator'] = attenuator_value

        if not self.canvas.point_exists(x, y, z):
            self._accept_point(ptargs)
            self.canvas.request_redraw()

    def _use_simple_render_changed(self):
        pts = self.canvas.get_points()
        for pi in pts:
            pi.use_simple_render = not self.use_simple_render
        self.canvas.request_redraw()

    def _spot_color_changed(self):
        pts = self.canvas.get_points()
        for pi in pts:
            pi.spot_color = self.spot_color
        self.canvas.request_redraw()

    def _spot_size_changed(self):
        pts = self.canvas.get_points()
        for pi in pts:
            pi.spot_size = self.spot_size
        self.canvas.request_redraw()

    def _get_controls(self):
        pass

    def traits_view(self):
        g = VGroup(
                HGroup(Item('accept_point', show_label=False),
                       Item('clear'), Item('clear_mode'), show_labels=False),
                Item('use_simple_render', label='Display Labels',
                     tooltip='Display labels or only a small spot'),
                Item('spot_color', label='Spot Color',
                     tooltip='Color for the point indicator spot'),
                Item('spot_size', label='Spot Size'))

        cg = self._get_controls()
        if cg:
            v = View(VSplit(cg, g))
        else:
            v = View(g)
        return v


class PointMaker(BaseMaker):
    def _accept_point(self, ptargs):
        npt = self.canvas.new_point(default_color=self.point_color,
                                    **ptargs)

        self.info('added point {}:{:0.5f},{:0.5f} z={:0.5f}'.format(npt.identifier, npt.x, npt.y, npt.z))


class FinishableMaker(BaseMaker):
    finish = Button

    #    accept_enabled = Bool(True)

    def _finish_fired(self):
        self.canvas.reset_markup()

    def traits_view(self):
        g = VGroup(
                Item('accept_point',
                     #                      enabled_when='accept_enabled',
                     show_label=False),
                HGroup(Item('clear'), Item('clear_mode'), show_labels=False),
                Item('finish', show_label=False))

        cg = self._get_controls()
        if cg:
            v = View(VGroup(cg, g))
        else:
            v = View(g)
        return v


class LineMaker(FinishableMaker):
    velocity = Float

    def _get_controls(self):
        return Item('velocity', label='Velocity mm/min')

    def _accept_point(self, ptargs):
        self.canvas.new_line_point(point_color=self.point_color,
                                   line_color=self.point_color,
                                   velocity=self.velocity,
                                   **ptargs)


class PolygonMaker(FinishableMaker):
    velocity = Float(1.0)
    use_convex_hull = Bool(True)
    scan_size = Int(50)
    use_outline = Bool
    offset = Int(50)
    find_min = Bool(True)

    def _get_controls(self):
        g = VGroup(Item('velocity', label='Velocity mm/min'),
                   Item('use_convex_hull'),
                   Item('scan_size', label='Scan H (um)'),
                   Item('find_min', label='Find Min. Lines'),
                   HGroup(Item('use_outline'), Item('offset', show_label=False, enabled_when='use_outline'))
                   )
        return g

    def _save(self):
        pe = self.stage_manager.points_programmer.polygon_entry

        polys = dict()
        for i, po in enumerate(self.canvas.get_polygons()):
            pts = []

            for pi in po.points:
                d = dict(identifier=pi.identifier,
                         z=float(pi.z),
                         #                        mask=pi.mask, attenuator=pi.attenuator,
                         xy=[float(pi.x), float(pi.y)])
                pts.append(d)

            # print int(pe) - 1, i
            if int(pe) - 1 == i:
                # save the selected polygon with new values
                v = self.velocity
                uch = self.use_convex_hull
                ss = self.scan_size
                o = self.offset
                uo = self.use_outline
                fm = self.find_min

                motors = dict()
                for motor in ('mask', 'attenuator'):
                    m = self.stage_manager.parent.get_motor(motor)
                    if m is not None:
                        motors[motor] = m.data_position

            else:
                p0 = po.points[-1]
                motors = dict(mask=p0.mask, attenuator=p0.attenuator)
                v = po.velocity
                uch = po.use_convex_hull
                ss = po.scan_size
                uo = po.use_outline
                o = po.offset
                fm = po.find_min

            polys[str(i)] = dict(points=pts,
                                 motors=motors,
                                 velocity=v,
                                 scan_size=ss,
                                 use_convex_hull=uch,
                                 use_outline=uo,
                                 offset=o,
                                 find_min=fm
                                 )

        return {'polygons': polys}

    def _use_convex_hull_changed(self):
        poly = self.canvas.polygons[-1]
        poly.use_convex_hull = self.use_convex_hull
        self.canvas.request_redraw()

    def _accept_point(self, ptargs):
        self.canvas.new_polygon_point(point_color=self.point_color,
                                      line_color=self.point_color,
                                      use_convex_hull=self.use_convex_hull,
                                      velocity=self.velocity,
                                      scan_size=self.scan_size,
                                      use_outline=self.use_outline,
                                      find_min=self.find_min,
                                      offset=self.offset,
                                      ptargs=ptargs)


class TransectMaker(FinishableMaker):
    step = Float(1, enter_set=True, auto_set=False)

    def _save(self):
        trans = []
        for tr in self.canvas.get_transects():
            pts = []

            for pi in tr.points:
                d = dict(identifier=pi.identifier,
                         z=float(pi.z),
                         mask=pi.mask,
                         attenuator=pi.attenuator,
                         xy=[float(pi.x), float(pi.y)],
                         offset_x=float(pi.offset_x),
                         offset_y=float(pi.offset_y), )
                pts.append(d)

            spts = []
            for pi in tr.step_points:
                d = dict(identifier=pi.identifier,
                         z=float(pi.z),
                         mask=pi.mask,
                         attenuator=pi.attenuator,
                         xy=[float(pi.x), float(pi.y)],
                         offset_x=float(pi.offset_x),
                         offset_y=float(pi.offset_y), )
                spts.append(d)

            trans.append(dict(points=pts,
                              step_points=spts,
                              step=tr.step))

        return {'transects': trans}

    def _get_controls(self):
        return Item('step', label='Step (mm)')

    def _step_changed(self):
        if self.step:
            self.canvas.set_transect_step(self.step)

    def _accept_point(self, ptargs):
        self.canvas.new_transect_point(point_color=self.point_color,
                                       line_color=self.point_color,
                                       step=self.step,
                                       **ptargs)


class GridOverlay(AbstractOverlay):
    ncols = Int
    nrows = Int
    vspacing = Float
    hspacing = Float
    indicator_width = Float
    indicator_height = Float
    rotation = Float
    current_pos = (0, 0)
    _cached_points = None
    points_invalid = True
    opacity = Float

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            comp = self.component
            gc.clip_to_rect(comp.x, comp.y,
                            comp.width, comp.height)
            pos = comp.get_offset_stage_screen_position()

            gc.translate_ctm(*pos)
            gc.rotate_ctm(math.radians(self.rotation))

            self._gather_points()
            gc.set_fill_color((0, 1, 0, self.opacity * 0.01))
            gc.set_stroke_color((0, 0, 0, self.opacity * 0.01))
            w, h = self.indicator_width, self.indicator_height
            w2, h2 = w / 2.0, h / 2.0
            for x, y in self._cached_points:
                gc.rect(x - w2 + 1, y - h2 + 1, w, h)
            gc.draw_path()

    def _gather_points(self):
        hspacing, vspacing = self.hspacing, self.vspacing

        if self._cached_points is None or self.points_invalid:
            ox, oy = 0, 0
            self._cached_points = []
            for ci in range(self.ncols):
                x = ox + ci * hspacing

                for ri in range(self.nrows):
                    y = oy + ri * vspacing

                    self._cached_points.append((x, y))
            self.points_invalid = False


class GridMaker(BaseMaker):
    ncols = Range(1, 40, 2, mode='spinner')
    nrows = Range(1, 40, 2, mode='spinner')

    vspacing = Float(800, enter_set=True, auto_set=False)
    hspacing = Float(800, enter_set=True, auto_set=False)
    grid_overlay = Instance(GridOverlay)
    toggle_grid_visible_button = Button
    indicator_size = Float(60, enter_set=True, auto_set=False)
    indicator_opacity = Range(0.0, 100., 75.)
    grid_indices = List
    rotation = Range(0.0, 360., 0.0, mode='slider')

    def __init__(self, *args, **kw):
        super(GridMaker, self).__init__(*args, **kw)
        self._add_grid_overlay()

    def clear_all_hook(self):
        self.grid_indices = []

    def initialize(self):
        self._add_grid_overlay()

    def deinitialize(self):
        if self.grid_overlay:
            self.grid_overlay.visible = False
            self.canvas.invalidate_and_redraw()

    def _add_grid_overlay(self):
        if not self.grid_overlay:
            w, h = self.canvas.get_wh(self.hspacing * .001,
                                      self.vspacing * .001)

            ind_s = self.indicator_size * .001
            # convert to screen
            iw, ih = self.canvas.get_wh(ind_s, ind_s)

            go = GridOverlay(component=self.canvas,
                             indicator_width=iw, indicator_height=ih,
                             hspacing=w, vspacing=h,
                             ncols=self.ncols, nrows=self.nrows,
                             opacity=self.indicator_opacity,
                             rotation=self.rotation)
            self.grid_overlay = go
            self.canvas.overlays.append(go)
        else:
            self.grid_overlay.visible = True

        self.canvas.invalidate_and_redraw()

    def _accept_point(self, ptargs):
        """
            only show the labels for first and last point

            outer loop is always max, inner loop min

            e.g cols=4, rows=2

             2 4 6 8
            +1 3 5 7

            cols=2, rows=4
            8 7
            6 5
            4 3
            2 1+

        """
        hspacing, vspacing = self.hspacing * 0.001, self.vspacing * 0.001
        ncols, nrows = self.ncols, self.nrows

        ox, oy = ptargs['xy']
        set_sig_figs = lambda v: float('{:0.3f}'.format(float(v)))

        vertical = ncols < nrows

        xs = max(ncols, nrows)
        ys = min(ncols, nrows)

        low_pc = self.canvas.point_count
        high_pc = low_pc + (ncols * nrows) - 1
        self.grid_indices.append((low_pc, low_pc + 1, high_pc - 1, high_pc))

        theta = math.radians(self.rotation)

        for ci in range(xs):
            if vertical:
                y = oy + ci * vspacing
            else:
                x = ox + hspacing * ci

            for ri in range(ys):

                if vertical:
                    x = ox + hspacing * ri
                else:
                    y = oy + ri * vspacing

                show_label = (ci == 0 and ri == 0) or (ci == (xs - 1) and ri == (ys - 1))

                xp = x * math.cos(theta) - y * math.sin(theta)
                yp = x * math.sin(theta) + y * math.cos(theta)

                xp, yp = set_sig_figs(xp), set_sig_figs(yp)
                ptargs['xy'] = (xp, yp)
                npt = self.canvas.new_point(default_color=self.point_color,
                                            show_label=show_label,
                                            redraw=False, **ptargs)

                self.info('added point {}:{:0.5f},{:0.5f} z={:0.5f}'.format(npt.identifier, npt.x, npt.y, npt.z))

        if high_pc > 40:
            self.canvas.downsample_point_labels(self.grid_indices)

        self.canvas.request_redraw()

    @on_trait_change('ncols, nrows')
    def _handle_grid_change(self, name, new):
        if self.grid_overlay:
            self.grid_overlay.trait_set(**{name: new})
            self.grid_overlay.points_invalid = True
            self.canvas.invalidate_and_redraw()

    @on_trait_change('hspacing, vspacing, indicator_size')
    def _handle_spacing_change(self, new):
        if self.grid_overlay:
            # convert to mm then to screen
            w, h = self.canvas.get_wh(self.hspacing * .001,
                                      self.vspacing * .001)

            # convert to mm
            ind_s = self.indicator_size * .001
            # convert to screen
            iw, ih = self.canvas.get_wh(ind_s, ind_s)

            self.grid_overlay.trait_set(hspacing=w,
                                        vspacing=h,
                                        indicator_width=iw,
                                        indicator_height=ih)
            self.grid_overlay.points_invalid = True
            self.canvas.invalidate_and_redraw()

    def _rotation_changed(self, new):
        if self.grid_overlay:
            self.grid_overlay.rotation = new
            self.canvas.invalidate_and_redraw()

    def _indicator_opacity_changed(self, new):
        if self.grid_overlay:
            self.grid_overlay.opacity = new
            self.canvas.invalidate_and_redraw()

    def _toggle_grid_visible_button_fired(self):
        if self.grid_overlay:
            self.grid_overlay.visible = not self.grid_overlay.visible
            self.canvas.invalidate_and_redraw()
        else:
            self._add_grid_overlay()

    def _get_controls(self):
        return VGroup(HGroup(Item('ncols', label='N. Cols'),
                             Item('nrows', label='N. Rows')),
                      HGroup(Item('hspacing', label='HSpacing (um)'),
                             Item('vspacing', label='VSpacing (um)')),
                      Item('rotation'),
                      Item('indicator_size', label='Indicator Size (um)'),
                      HGroup(UItem('toggle_grid_visible_button', label='Toggle Grid'),
                             Item('indicator_opacity', label='Opacity')))

# ============= EOF =============================================
