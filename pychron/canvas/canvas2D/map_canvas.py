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
from traits.api import Instance, Bool, Enum, Float
#=============standard library imports ========================
import math
#=============local library imports  ==========================
from pychron.lasers.stage_managers.stage_map import StageMap
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas
from pychron.canvas.canvas2D.scene.primitives.primitives import CalibrationObject
from pychron.core.geometry.affine import AffineTransform

class MapCanvas(SceneCanvas):
    _map = Instance(StageMap)
    calibration_item = Instance(CalibrationObject)
    calibrate = Bool(False)
    hole_color = (0, 0, 0)
    show_grids = False
    show_axes = False

    render_map = Bool(False)
    hole_crosshairs_kind = Enum(1, 2)
    hole_crosshairs_color = Enum('red', 'green', 'blue', 'yellow', 'black')
    current_hole = None
    bitmap_scale = Float(1.0)

    use_valid_holes = Bool(True)
    show_indicators = Bool(True)

    scaling = Float(1.0)


#    def normal_key_pressed(self, event):
# #        super(MapCanvas, self).normal_key_pressed(event)
#
#        if event.handled:
#            pass
#        elif self.current_hole is not None and event.character == 'Backspace':
#            self.calibration_item.tweak_dict.pop(self.current_hole)


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

#    def new_calibration_item(self, x, y, rotation):
    def new_calibration_item(self):
#        if kind in ['MassSpec', 'pychron-auto']:
#            ci = CalibrationObject()
#        else:
#            ci = CalibrationItem(x, y, rotation, canvas=self)

        ci = CalibrationObject()
        self.calibration_item = ci
        return ci

    def set_map(self, mp):
        self._map = mp
        self._map.on_trait_change(self.request_redraw, 'g_shape')
        self._map.on_trait_change(self.request_redraw, 'g_dimension')

    def _draw_hook(self, gc, *args, **kw):
        if self.render_map:
            self._draw_map(gc)
        super(MapCanvas, self)._draw_hook(gc, *args, **kw)

    def _draw_map(self, gc, *args, **kw):
        gc.save_state()
        mp = self._map
        if mp is not None:
            ca = self.calibration_item

            if ca:
                ox, oy = self.map_screen([(0, 0)])[0]

                cx, cy = self.map_screen([ca.center])[0]

                rot = ca.rotation

                gc.translate_ctm(cx, cy)
                gc.rotate_ctm(math.radians(rot))
                gc.translate_ctm(-cx , -cy)

                gc.translate_ctm(cx - ox, cy - oy)

            gshape = mp.g_shape
            get_draw_func = lambda x: getattr(self, '_draw_{}'.format(x))
            func = get_draw_func(gshape)
            map_screen = self.map_screen
            draw_sample_hole = self._draw_sample_hole
            for hole in mp.sample_holes:
                tweaked = False
                if ca:
                    tweaked = hole.id in ca.tweak_dict

                if hole.render.lower() == 'x' or tweaked or not self.use_valid_holes:

                    tweak = None
#                    if ca is not None:

#                        if str(hole.id) in ca.tweak_dict and isinstance(ca, CalibrationItem):
#                            tweak = ca.tweak_dict[str(hole.id)]

                    x, y = map_screen([(hole.x, hole.y)])[0]

                    if hole.shape != gshape:
                        func = get_draw_func(hole.shape)

                    draw_sample_hole(gc, x + 1, y + 1, hole.dimension,
                                           func, tweak=tweak)

        gc.restore_state()

    def _draw_sample_hole(self, gc, x, y, size, func, tweak=None):
        '''

        '''
        gc.set_stroke_color(self.hole_color)

        if self.hole_crosshairs_kind != 2:
            if self.show_indicators:
                f = self._draw_cross_indicator
                f(gc, x, y, float(size), tweak=tweak)
        func(gc, x, y, float(size))

    def _draw_cross_indicator(self, gc, x, y, size, tweak=None):
        w, h = self._get_wh(size, size)
        w /= 2.0
        h /= 2.0
        gc.save_state()

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

        gc.restore_state()

    def _draw_circle(self, gc, x, y, diam):
        '''

        '''
        pts = self.map_screen([(diam / 2.0, 0), (0, 0)])
        rad = pts[0][0] - pts[1][0]

        gc.arc(x, y, rad, 0, 360)
        gc.draw_path()

    def _draw_square(self, gc, x, y, size):
        '''
 
        '''
        w, h = self._get_wh(size, size)
        gc.rect(x - w / 2.0, y - h / 2.0, w, h)
        gc.draw_path()


# ============= EOF =============================================
