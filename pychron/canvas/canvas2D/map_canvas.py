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

# =============enthought library imports=======================
from traits.api import Instance, Bool, Enum, Float, Color
# =============standard library imports ========================
import math
# =============local library imports  ==========================
from pychron.stage.maps.base_stage_map import BaseStageMap
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas
from pychron.canvas.canvas2D.scene.primitives.primitives import CalibrationObject
from pychron.core.geometry.affine import AffineTransform


class MapCanvas(SceneCanvas):
    _map = Instance(BaseStageMap)
    calibration_item = Instance(CalibrationObject)
    calibrate = Bool(False)
    hole_color = Color('white')
    # show_grids = False
    # show_axes = False

    render_map = Bool(False)
    render_calibrated = Bool(False)
    hole_crosshairs_kind = Enum(1, 2)
    hole_crosshairs_color = Enum('red', 'green', 'blue', 'yellow', 'black')
    current_hole = None
    bitmap_scale = Float(1.0)

    use_valid_holes = Bool(True)
    show_indicators = Bool(True)

    scaling = Float(1.0)

    # def __init__(self, *args, **kw):
    #     super(MapCanvas, self).__init__(*args, **kw)

    def normal_left_down(self, event):
        super(MapCanvas, self).normal_left_down(event)

        if self.current_hole is not None:
            # and not event.handled
            ca = self.calibration_item
            if ca is not None:
                if hasattr(event, 'item'):
                    if hasattr(ca, 'right'):
                        if event.item.right is ca.right:
                            return

                rot = ca.rotation
                cpos = ca.center

                aff = AffineTransform()
                aff.translate(*cpos)
                aff.rotate(rot)
                aff.translate(-cpos[0], -cpos[1])
                aff.translate(*cpos)

                mpos = self.mp.get_hole_pos(self.current_hole)
                #                dpos = aff.transformPt(mpos)
                dpos = aff.transform(*mpos)
                spos = self.map_data((event.x, event.y))

                # not much point in adding an indicator because the hole
                # renders its own
                # self.markupdict['tweak'] = Indicator(*spos, canvas = self)

                tweak = spos[0] - dpos[0], spos[1] - dpos[1]
                ca.tweak_dict[self.current_hole] = tweak

                self.request_redraw()

    def normal_mouse_move(self, event):
        # over a hole
        ca = self.calibration_item
        if ca:

            for obj in self.mp.sample_holes:
                hole = obj.id
                pos = obj.x, obj.y

                rot = ca.rotation
                cpos = ca.center

                aff = AffineTransform()
                aff.translate(*cpos)
                aff.rotate(rot)
                aff.translate(-cpos[0], -cpos[1])
                aff.translate(*cpos)
                dpos = aff.transformPt(pos)

                pos = self.map_screen([dpos])[0]
                if abs(pos[0] - event.x) <= 10 and abs(pos[1] - event.y) <= 10:
                    event.window.set_pointer(self.select_pointer)
                    event.handled = True
                    self.current_hole = hole
                    break

        if not event.handled:
            self.current_hole = None
            super(MapCanvas, self).normal_mouse_move(event)

    def new_calibration_item(self):
        ci = CalibrationObject()
        self.calibration_item = ci
        return ci

    def set_map(self, mp):
        self._map = mp
        self._map.on_trait_change(self.request_redraw, 'g_shape')
        self._map.on_trait_change(self.request_redraw, 'g_dimension')

    def _draw_underlay(self, gc, *args, **kw):
        if self.render_map:
            self._draw_map(gc)
        super(MapCanvas, self)._draw_underlay(gc, *args, **kw)

    def _convert_color(self, color):
        rgb = lambda x: 0 <= x <= 1.

        if not isinstance(color, (list, tuple)):
            color = color.toTuple()

        if not all(map(rgb, color)):
            f = lambda x: x / 255.
            color = map(f, color)
        return color

    def _draw_map(self, gc, *args, **kw):
        with gc:
            mp = self._map
            if mp is not None:
                ca = self.calibration_item
                if self.render_calibrated and ca:
                    ox, oy = self.map_screen([(0, 0)])[0]

                    cx, cy = self.map_screen([ca.center])[0]

                    rot = ca.rotation

                    gc.translate_ctm(cx, cy)
                    gc.rotate_ctm(math.radians(rot))
                    gc.translate_ctm(-cx, -cy)

                    gc.translate_ctm(cx - ox, cy - oy)

                gshape = mp.g_shape

                get_draw_func = lambda x: getattr(self, '_draw_{}'.format(x))
                func = get_draw_func(gshape)

                w, h = self._get_wh(mp.g_dimension, mp.g_dimension)

                map_screen = self.map_screen
                draw_sample_hole = self._draw_sample_hole

                gc.set_fill_color(self._convert_color(self.hole_color))

                for hole in mp.sample_holes:
                    with gc:
                        tweaked = False
                        if ca:
                            tweaked = hole.id in ca.tweak_dict

                        if hole.render.lower() == 'x' or tweaked or not self.use_valid_holes:
                            tweak = None

                            x, y = map_screen([(hole.x, hole.y)])[0]

                            if hole.shape != gshape:
                                func = get_draw_func(hole.shape)
                            if float(hole.dimension) != mp.g_dimension:
                                w, h = self._get_wh(hole.dimension, hole.dimension)
                            if hole.analyzed:
                                gc.set_fill_color((1, 0, 0))

                            draw_sample_hole(gc, x, y, w, h, func, tweak=tweak)

    def _draw_sample_hole(self, gc, x, y, w, h, func, tweak=None):
        if self.hole_crosshairs_kind != 2:
            if self.show_indicators:
                f = self._draw_cross_indicator
                f(gc, x, y, w, h, tweak=tweak)
        func(gc, x, y, w, h)

    def _draw_cross_indicator(self, gc, x, y, w, h, tweak=None):
        # w, h = self._get_wh(size, size)
        w /= 2.0
        h /= 2.0
        with gc:

            ca = self.calibration_item
            if ca:
                # make the crosshairs orthogonal
                gc.translate_ctm(x, y)
                gc.rotate_ctm(math.radians(-ca.rotation))
                gc.translate_ctm(-x, -y)

            if tweak:
                gc.translate_ctm(*self._get_wh(*tweak))

            gc.set_stroke_color((1, 1, 0))

            gc.move_to(x - w, y)
            gc.line_to(x + w, y)
            gc.draw_path()

            gc.move_to(x, y - h)
            gc.line_to(x, y + h)
            gc.draw_path()

    def _draw_circle(self, gc, x, y, w, h):
        # pts = self.map_screen([(diam / 2.0, 0), (0, 0)])
        # rad = pts[0][0] - pts[1][0]

        gc.arc(x, y, w / 2., 0, 360)
        gc.draw_path()

    def _draw_square(self, gc, x, y, w, h):
        # w, h = self._get_wh(size, size)
        gc.rect(x - w / 2.0, y - w / 2.0, w, w)
        gc.draw_path()

    def _show_grids_default(self):
        return False

    def _show_axes_default(self):
        return False

# ============= EOF =============================================
