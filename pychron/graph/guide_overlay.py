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
from chaco.api import AbstractOverlay
from enable.colors import ColorTrait
from enable.enable_traits import LineStyle
from enable.label import Label
from enable.tools.drag_tool import DragTool
from traits.api import Enum, Float, Instance


# =============standard library imports ========================

# =============local library imports  ==========================


class GuideOverlayMoveTool(DragTool):
    hit_length = 5

    def is_draggable(self, x, y):
        ov = self.overlay

        if ov.orientation == 'v':
            mapper = ov.component.index_mapper
            cv = x
        else:
            mapper = ov.component.value_mapper
            cv = y

        v = mapper.map_screen(ov.value)
        return abs(cv - v) < self.hit_length

    def dragging(self, event):
        ov = self.overlay
        if ov.orientation == 'v':
            v = event.x
            mapper = ov.component.index_mapper
        else:
            v = event.y
            mapper = ov.component.value_mapper

        ov.value = mapper.map_data(v)
        ov.display_value = True
        ov.label_position = (event.x + 5, event.y + 5)
        ov.invalidate_and_redraw()

    def drag_end(self, event):
        self.overlay.display_value = False
        self.overlay.invalidate_and_redraw()

    def drag_cancel(self, event):
        self.drag_end(event)


class GuideOverlay(AbstractOverlay):
    """
    draws a horizontal or vertical line at the specified value
    """
    orientation = Enum('h', 'v')
    value = Float
    color = ColorTrait("red")
    line_style = LineStyle('dash')
    line_width = Float(1)
    display_value = False

    label = Instance(Label, ())

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        with gc:
            gc.clip_to_rect(component.x, component.y, component.width, component.height)
            with gc:
                gc.set_line_dash(self.line_style_)
                gc.set_line_width(self.line_width)
                gc.set_stroke_color(self.color_)
                gc.begin_path()

                if self.orientation == 'h':
                    x1 = component.x
                    x2 = component.x2
                    y1 = y2 = component.value_mapper.map_screen(self.value)
                else:
                    y1 = component.y
                    y2 = component.y2
                    x1 = x2 = component.index_mapper.map_screen(self.value)

                gc.move_to(x1, y1)
                gc.line_to(x2, y2)
                gc.stroke_path()

            if self.display_value:
                with gc:
                    l = self.label
                    l.text = '{:0.5f}'.format(self.value)
                    l.position = self.label_position
                    l.draw(gc)

# ============= EOF =====================================
