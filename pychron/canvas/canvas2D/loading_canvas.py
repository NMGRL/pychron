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

# ===============================================================================
# Copyright 2013 Jake Ross
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
from enable.abstract_overlay import AbstractOverlay
from kiva import Font
from traits.api import Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas
from pychron.canvas.canvas2D.scene.loading_scene import LoadingScene


def group_position(pos, func=None):
    pos = sorted(pos)
    pp = pos[0]
    stack = [pp]
    ss = []

    for pi in pos[1:]:
        if not pp + 1 == pi:
            ss.append(func(stack) if func else stack)
            stack = []

        stack.append(pi)
        pp = pi

    if stack:
        ss.append(func(stack) if func else stack)
    return ss


class LoadingOverlay(AbstractOverlay):
    info_str = ''
    font = Font('Arial')

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        if self.info_str:
            with gc:
                gc.set_font(self.font)
                lines = self.info_str.split('\n')
                lws, lhs = zip(*[gc.get_full_text_extent(mi)[:2] for mi in lines])
                rect_width = max(lws) + 4
                rect_height = (max(lhs) + 2) * len(lhs)

                gc.translate_ctm(self.x + 15, self.y - rect_height)
                gc.set_fill_color((0.7, 0.7, 0.7))
                gc.rect(-3, -3, rect_width + 6, rect_height + 6)
                gc.draw_path()

                gc.set_fill_color((0, 0, 0))

                lh = max(lhs) + 2
                for i, li in enumerate(lines[::-1]):
                    gc.set_text_position(0, i * lh)
                    gc.show_text(li)

    def set_item(self, item):
        if item and item.fill:
            self.info_str = 'hole: {}\nlabnumber: {}\nweight: {}mg\nnote: {}'.format(item.name,
                                                                                     item.labnumber_label.text,
                                                                                     item.weight_label.text,
                                                                                     item.note)

        else:
            self.info_str = ''


class LoadingCanvas(SceneCanvas):
    use_pan = False
    use_zoom = False
    selected = Any
    # fill_padding = True
    # bgcolor = 'red'
    show_axes = False
    show_grids = False

    padding_top = 0
    padding_bottom = 0
    padding_left = 0
    padding_right = 0

    aspect_ratio = 1
    editable = True
    _scene_klass = LoadingScene

    current_item = None
    popup = None

    _last_position = 1

    def load_scene(self, t, **kw):
        self.overlays = []
        scene = self._scene_klass()
        scene.load(t, **kw)

        self.view_x_range = scene.get_xrange()
        self.view_y_range = scene.get_yrange()

        self.scene = scene
        self.popup = LoadingOverlay()
        self.popup.visible = False

        self.overlays.append(self.popup)

    def get_selection(self):
        return [item for item in self.scene.get_items(LoadIndicator) if item.state]

    def edit_left_down(self, event):
        if self.editable:
            self.selected = self.hittest(event)
            self.selected.state = not self.selected.state
            self.request_redraw()

    def normal_left_down(self, event):
        sel = self.hittest(event)
        if sel:
            if self.editable:
                self.selected = sel
                # self._counter = int(sel.name)+1
            else:
                sel.state = not sel.state
                self.selected = sel

        self.request_redraw()
        self.selected = None

    def hittest(self, event):
        if self.scene:
            for li in self.scene.layers:
                for it in li.components:
                    # it.canvas = self
                    if it.is_in(event.x, event.y):
                        return it

    def normal_mouse_leave(self, event):
        pass

    def normal_mouse_move(self, event):

        if self.editable:
            self.current_item = self.hittest(event)
            if self.current_item:
                event.window.set_pointer(self.cross_pointer)
            else:
                self._set_normal_pointer(event)

    def set_last_position(self, pos):
        self._last_position = pos

    def normal_key_pressed(self, event):
        if event.character == 'Enter':
            self.selected = self.scene.get_item(str(self._last_position), klass=LoadIndicator)
        self.request_redraw()

    def info_left_down(self, event):
        self.edit_left_down(event)

    def info_mouse_move(self, event):
        self.popup.x, self.popup.y = event.x, event.y
        self.current_item = self.hittest(event)
        if self.current_item:

            event.window.set_pointer(self.pointer)
            self.popup.set_item(self.current_item)
            self.popup.visible = True
        else:
            self.popup.visible = False
            self._set_normal_pointer(event)

        self.request_redraw()

    def info_mouse_leave(self, event):
        self.popup.visible = False
        self.request_redraw()

    def _set_normal_pointer(self, event):
        event.window.set_pointer(self.normal_pointer)

        # def _pop(self):
        # self.popup.set_item(self.current_item)
        # self.popup.visible = True
        # self.request_redraw()

# ============= EOF =============================================
