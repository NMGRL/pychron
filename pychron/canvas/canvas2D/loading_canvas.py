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
from chaco.overlays.plot_label import PlotLabel
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
from kiva.fonttools import str_to_font
from traits.api import Any, Event, Enum
import time
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.loading_scene import LoadingScene
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas


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


class ModeOverlay(AbstractOverlay):
    mode = Enum('Entry', 'Goto', 'GotoEntry', 'FootPedal')

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            # x = self.x
            # y = self.y
            y2 = other_component.y2
            x = other_component.x
            w = other_component.width
            states = ('Entry', 'Goto', 'GotoEntry', 'FootPedal')
            n = len(states)
            ww = n * 100 + 5 * n / 2
            gc.translate_ctm((w - ww) / 2 + x, y2 - 20)
            for i, state in enumerate(states):
                with gc:
                    self._render_state(gc, i, state)

    def _render_state(self, gc, idx, state):

        gc.set_stroke_color((0, 0, 0))
        w = 100
        x = idx * w
        gc.set_font(str_to_font('arial 12'))
        gc.set_text_position(x + 2, 2)
        gc.show_text(state)
        gc.rect(x, 0, w - 5, 20)
        if self.mode == state:
            gc.set_fill_color((0, 0.5, 0, 0.1))
            gc.draw_path()
        else:
            gc.stroke_path()


class LoadingOverlay(AbstractOverlay):
    info_str = ""
    font = Font("Arial")

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        if self.info_str:
            with gc:
                gc.set_font(self.font)
                lines = self.info_str.split("\n")
                lws, lhs = list(zip(*[gc.get_full_text_extent(mi)[:2] for mi in lines]))
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
            msg = "hole: {}\nlabnumber: " "{}\nweight: {}mg\nnote: {}".format(
                item.name, item.labnumber_label.text, item.weight_label.text, item.note
            )
            self.info_str = msg

        else:
            self.info_str = ""

class LoadingStatusOverlay(PlotLabel):
    pass


class LoadingCanvas(SceneCanvas):
    use_pan = False
    use_zoom = False
    selected = Any
    increment_event = Event
    focus_event = Event
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
    scene_klass = LoadingScene

    current_item = None
    popup = None

    _last_position = 1
    _foot_pedal_mode = False

    mode_overlay_enabled = True
    mode_overlay = None

    def load_scene(self, t, **kw):
        self.overlays = []
        scene = self.scene_klass()
        scene.load(t, **kw)

        self.view_x_range = scene.get_xrange()
        self.view_y_range = scene.get_yrange()
        self.scene = scene
        self.popup = LoadingOverlay()
        self.popup.visible = False
        self.overlays.append(self.popup)

        if self.mode_overlay_enabled:
            self.mode_overlay = ModeOverlay()
            self.overlays.append(self.mode_overlay)

        self.status_overlay = LoadingStatusOverlay(component=self,
                                                   overlay_position="inside bottom",
                                                   bgcolor='transparent')

        self.overlays.append(self.status_overlay)

    def set_foot_pedal_mode(self, v):
        self._foot_pedal_mode = v

    def set_status_text(self, identifier='', sample='', position='', count=0, max_count=0):
        if self.mode_overlay.mode == 'FootPedal':
            sttext = f'Identifier: {identifier}\n' \
                     f'Sample: {sample}\n' \
                     f'Position: {position}'\
                     f'Count: {count}/{max_count}'

            self.status_overlay.text = sttext

    def get_selection(self):
        return [item for item in self.scene.get_items(LoadIndicator) if item.state]

    # def edit_left_down(self, event):
    #     if self.editable:
    #         sel = self.hittest(event)
    #         if sel:
    #             sel.state = not sel.state
    #
    #         self.selected = sel
    #
    #         # self.selected = self.hittest(event)
    #         # self.selected.state = not self.selected.state
    #         self.request_redraw()
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
                    if it.canvas and it.is_in(event.x, event.y):
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

    _last_key_press = 0
    _last_key_release = 0

    def normal_key_released(self, event):
        if not self._last_key_release or time.time() - self._last_key_release > 1:
            self._last_key_release = time.time()
            if event.character in (' ', 'a') and self._foot_pedal_mode:
                self.increment_event = True
                return

    def normal_key_pressed(self, event):
        print('fff', event.character)
        if not self._last_key_press or time.time() - self._last_key_press > 0.1:
            if event.character in ('f', 'g', 'Up', 'Down'):
                self._last_key_press = time.time()
                if event.character == 'f':
                    self.focus_event = 'Up'
                elif event.character == 'g':
                    self.focus_event = 'Down'
                elif event.character in ('Up', 'Down'):
                    self.focus_event = event.character
                return

        if self._foot_pedal_mode:
            return

        if event.character == "Enter":
            self.selected = self.scene.get_item(
                str(self._last_position), klass=LoadIndicator
            )
        self.request_redraw()

    # def info_left_down(self, event):
    #     self.edit_left_down(event)
    #
    # def info_mouse_move(self, event):
    #     self.popup.x, self.popup.y = event.x, event.y
    #     self.current_item = self.hittest(event)
    #     if self.current_item:
    #
    #         event.window.set_pointer(self.pointer)
    #         self.popup.set_item(self.current_item)
    #         self.popup.visible = True
    #     else:
    #         self.popup.visible = False
    #         self._set_normal_pointer(event)
    #
    #     self.request_redraw()
    #
    # def info_mouse_leave(self, event):
    #     self.popup.visible = False
    #     self.request_redraw()

    def _set_normal_pointer(self, event):
        event.window.set_pointer(self.normal_pointer)

        # def _pop(self):
        # self.popup.set_item(self.current_item)
        # self.popup.visible = True
        # self.request_redraw()

# ============= EOF =============================================
