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
from traits.api import Float, Instance, Str, Tuple, Event
from chaco.abstract_overlay import AbstractOverlay
from enable.base_tool import BaseTool
from enable.colors import ColorTrait
# ============= standard library imports ========================
import string
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.pipeline.plot.overlays.mean_indicator_overlay import XYPlotLabel


class LimitsTool(BaseTool):
    ruler_pos = Tuple
    ruler_data_pos = Float
    orientation = 'x'
    active = False

    entered_value = Str
    limits_updated = Event

    def _set_entered_value(self, c):
        if c == '.' or c in string.digits:
            self.entered_value += c
        elif c in ('Backspace', 'Delete'):
            self.entered_value = self.entered_value[:-1]

    def drag_key_pressed(self, event):
        c = event.character
        if c == 'Esc':
            self._finish(event)
        else:
            self._set_entered_value(c)
            self.event_state = 'manual_set' if self.entered_value else 'drag'
        self.component.request_redraw()

    def manual_set_key_pressed(self, event):
        c = event.character
        if c == 'Enter':
            self._finish(event)
            try:
                self._set_data_value(float(self.entered_value))
            except ValueError:
                pass

            self.entered_value = ''
        else:
            self._set_entered_value(c)

        self.component.request_redraw()

    def is_draggable(self, event):
        tol = 5
        if self.orientation == 'x':
            return abs(event.x - self.component.x) < tol or abs(event.x - self.component.x2) < tol
        else:
            return abs(event.y - self.component.y) < tol or abs(event.y - self.component.y2) < tol

    def normal_left_down(self, event):
        if self.is_draggable(event):
            self.event_state = 'drag'
            self.pointer = 'hand'
            event.window.set_pointer(self.pointer)
            if self.orientation == 'x':
                a = event.x
                b = self.component.x
                b2 = self.component.x2
            else:
                a = event.y
                b = self.component.y
                b2 = self.component.y2

            if abs(a - b) < abs(a - b2):
                self._dsign = 'low'
            else:
                self._dsign = 'high'

            self._set_ruler_pos(event)
            self.component.request_redraw()
            event.handled = True

    def _set_ruler_pos(self, v):
        self.ruler_pos = (v.x, v.y)
        v = getattr(v, self.orientation)
        self.ruler_data_pos = self._map_value(v - 0.25)

    def drag_left_up(self, event):
        self._finish(event)
        v = event.x if self.orientation == 'x' else event.y
        self._set_value(v)
        event.handled = True

    def _finish(self, event):
        self.event_state = 'normal'
        self.pointer = 'arrow'
        event.window.set_pointer(self.pointer)

        self.ruler_pos = tuple()
        self.limits_updated = True

    def drag_mouse_move(self, event):
        self._set_ruler_pos(event)
        if self.orientation == 'x':
            a = event.x
            b = self.component.x
            b2 = self.component.x2
        else:
            a = event.y
            b = self.component.y
            b2 = self.component.y2

        if a < b or a > b2:
            self._set_value(a)
        self.component.request_redraw()
        event.handled = True

    def _set_value(self, screen_val):
        v = self._map_value(screen_val)
        self._set_data_value(v)

    def _set_data_value(self, v):
        if self.orientation == 'x':
            r = self.component.index_range
        else:
            r = self.component.value_range

        if self._dsign == 'low':
            if getattr(r, 'high') > v:
                r.trait_set(**{'{}_setting'.format(self._dsign): v})
        else:
            if getattr(r, 'low') < v:
                r.trait_set(**{'{}_setting'.format(self._dsign): v})

        self.component.request_redraw()

    def _map_value(self, v):
        if self.orientation == 'x':
            m = self.component.index_mapper
        else:
            m = self.component.value_mapper

        return m.map_data(v)


class LimitOverlay(AbstractOverlay):
    tool = LimitsTool
    label = Instance(XYPlotLabel)
    color = ColorTrait('red')
    label_manual_color = ColorTrait('tomato')
    label_bgcolor = ColorTrait('lightblue')

    def _label_default(self):
        return XYPlotLabel(component=self.component,
                           bgcolor=self.label_bgcolor,
                           # border_width = LabelDelegate
                           border_color='black',
                           # border_visible = LabelDelegate
                           border_visible=True)

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):

        tool = self.tool
        y, y2 = other_component.y, other_component.y2
        x, x2 = other_component.x, other_component.x2

        if tool.ruler_pos:
            a, b = tool.ruler_pos
            if tool.orientation == 'x':
                x, x2 = a, a
                self.label.sx = x
                self.label.sy = b + 10
            else:
                y, y2 = b, b
                self.label.sx = a + 20
                self.label.sy = y

            with gc:
                gc.set_stroke_color(self.color_)
                gc.set_line_width(2)
                gc.lines([(x, y), (x2, y2)])
                gc.stroke_path()

            if tool.entered_value:
                self.label.bgcolor = self.label_manual_color
                v = tool.entered_value
            else:
                self.label.bgcolor = self.label_bgcolor
                v = floatfmt(tool.ruler_data_pos)

            self.label.text = '{}: {}'.format(tool.orientation.upper(), v)
            self.label.overlay(other_component, gc, view_bounds=None, mode="normal")

# ============= EOF =============================================
