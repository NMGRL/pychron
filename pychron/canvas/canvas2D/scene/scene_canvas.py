# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
try:
    from kiva import JOIN_ROUND
except ImportError:
    JOIN_ROUND = 0
from traits.api import Instance, Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from pychron.canvas.canvas2D.scene.scene import Scene


class SceneCanvas(BaseDataCanvas):
    scene = Instance(Scene)
    scene_klass = Any

    def __init__(self, *args, **kw):
        super(SceneCanvas, self).__init__(*args, **kw)
        self.border_visible = True
        self.border_color = 'lightgray'
        self.border_width = 5

    def clear_all(self):
        if self.scene:
            self.scene.reset_layers()

    def show_all(self):
        if self.scene:
            for li in self.scene.layers:
                li.visible = True
            self.request_redraw()

    def hide_all(self):
        if self.scene:
            for li in self.scene.layers:
                li.visible = False
            self.request_redraw()

    # private
    def _draw_underlay(self, gc, view_bounds=None, mode="normal"):
        if self.scene:
            self.scene.render_components(gc, self)
        super(SceneCanvas, self)._draw_underlay(gc, view_bounds, mode)

    def _draw_overlay(self, gc, *args, **kw):
        super(SceneCanvas, self)._draw_overlay(gc, *args, **kw)
        if self.scene:
            self.scene.render_overlays(gc, self)

    def _draw_inset_border(self, gc, view_bounds=None, mode="default"):
        if not self.border_visible:
            return

        border_width = self.border_width
        with gc:
            gc.set_line_width(border_width)
            gc.set_line_dash(self.border_dash_)
            gc.set_stroke_color(self.border_color_)
            gc.set_antialias(0)
            gc.set_line_join(JOIN_ROUND)
            offset = self.border_width
            gc.move_to(self.x+offset, self.y+offset)
            gc.line_to(self.x+offset, self.y2-offset)
            gc.line_to(self.x2-offset, self.y2-offset)
            gc.line_to(self.x2-offset, self.y+offset)
            gc.line_to(self.x+offset, self.y+offset)
            gc.line_to(self.x+offset, self.y2-offset)
            gc.close_path()
            gc.stroke_path()

    # handlers
    def _scene_changed(self, name, old, new):
        if new:
            new.on_trait_change(self.request_redraw, 'layout_needed')
        if old:
            old.on_trait_change(self.request_redraw,
                                'layout_needed', remove=True)

    def _scene_default(self):
        return self.scene_klass()
# ============= EOF =============================================
