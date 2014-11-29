# ===============================================================================
# Copyright 2013 Jake Ross
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
import string

from chaco.tools.data_label_tool import DataLabelTool
from chaco.tooltip import ToolTip
from enable.colors import transparent_color
from traits.api import Str, List


# ============= standard library imports ========================
# ============= local library imports  ==========================
VK = string.ascii_letters

KEY_MAP = {'Enter': '\n', ' ': ' '}


class AnnotationTool(DataLabelTool):
    active = True
    components = List

    def normal_key_pressed(self, event):
        if self.active:
            c = event.character
            label = self.component
            if not label.visible:
                label.x, label.y = self.current_mouse_pos

            if c == 'Backspace':
                if self.component and self.component.selected:
                    pcomp = self.component.component
                    pcomp.overlays.remove(self.component)
                    if len(self.components) > 1:
                        self.components.remove(self.component)
                        self.component = self.components[0]
                    else:
                        self.component.text = ''
                    pcomp.request_redraw()
                else:
                    label.text = label.text[:-1]

            elif c in KEY_MAP:
                label.text += KEY_MAP[c]
            elif c in VK:
                label.text += c

            event.handled = True

    def normal_left_down(self, event):
        x, y = event.x, event.y

        if not self.component.text:
            self.active = True
        elif not self.is_draggable(x, y):
            self.active = False

    def normal_left_dclick(self, event):
        x, y = event.x, event.y
        if not self.is_draggable(x, y):
            self.component.selected = False
        else:
            self.component.selected = True
            self.active = True

        self.component.request_redraw()

    def is_draggable(self, x, y):
        """ Returns whether the (x,y) position is in a region that is OK to
        drag.

        Overrides DragTool.
        """
        if self.components:
            for label in self.components:
                hit = (label.x <= x <= label.x2 and \
                       label.y <= y <= label.y2)
                if hit:
                    self.component = label
                    return True
            else:
                return False
        else:
            return False

    def normal_mouse_move(self, event):
        self.current_mouse_pos = (event.x, event.y)

    def drag_start(self, event):
        """ Called when the drag operation starts.

        Implements DragTool.
        """
        if self.component:
            label = self.component
            self._original_offset = (label.x, label.y)
            event.window.set_mouse_owner(self, event.net_transform())
            event.handled = True
        return

    def dragging(self, event):
        """ This method is called for every mouse_move event that the tool
        receives while the user is dragging the mouse.

        Implements DragTool. Moves and redraws the label.
        """
        if self.component:
            label = self.component
            dx = int(event.x - self.mouse_down_position[0])
            dy = int(event.y - self.mouse_down_position[1])

            label.x, label.y = (self._original_offset[0] + dx,
                                self._original_offset[1] + dy)

            event.handled = True
            label.request_redraw()
        return


def rounded_rect(gc, x, y, width, height, corner_radius):
    with gc:
        gc.translate_ctm(x, y)  # draw a rounded rectangle
        x = y = 0
        gc.begin_path()

        hw = width * 0.5
        hh = height * 0.5
        if hw < corner_radius:
            corner_radius = hw * 0.5
        elif hh < corner_radius:
            corner_radius = hh * 0.5

        gc.move_to(x + corner_radius, y)
        gc.arc_to(x + width, y, x + width, y + corner_radius, corner_radius)
        gc.arc_to(x + width, y + height, x + width - corner_radius, y + height, corner_radius)
        gc.arc_to(x, y + height, x, y, corner_radius)
        gc.arc_to(x, y, x + width + corner_radius, y, corner_radius)
        gc.stroke_path()


class AnnotationOverlay(ToolTip):
    text = Str('')
    visible = False
    selected = False

    def _text_changed(self):
        self.visible = bool(self.text)
        self.lines = self.text.split('\n')
        self.component.invalidate_and_redraw()

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        super(AnnotationOverlay, self).overlay(component, gc, view_bounds=None, mode='normal')

        if self.selected:
            dash = [10, 0]
            inset = 0
            color = (1, 0, 0)
            bgcolor = transparent_color
            marker_size = 0
            x, y = self.x, self.y
            w, h = self.width, self.height

            self.draw_select_box(gc, (x, y), (w, h),
                                 2,
                                 dash, inset, color, bgcolor,
                                 marker_size
            )

            #def _draw_selection(self, gc, view_bounds=None, mode="normal"):
            #    (self, gc, view_bounds=None, mode="default",
            #                 force_draw=False):
            #
            #    if not self.border_visible:
            #        return
            #
            #    if self.overlay_border or force_draw:
            #        border_width = self.border_width
            #        with gc:
            #            gc.set_line_width(border_width)
            #            gc.set_line_dash(self.border_dash_)
            #            gc.set_stroke_color(self.border_color_)
            #            rounded_rect(gc, self.x, self.y, self.width, self.height, 4)


# ============= EOF =============================================
