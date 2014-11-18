# ===============================================================================
# Copyright 2014 Jake Ross
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
from enable.base_tool import BaseTool
from traits.trait_types import Event, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================


class MarkerTool(BaseTool):
    label_with_intensity = Bool(True)

    overlay = None
    underlay = None
    text = ''

    marker_added = Event
    use_vertical_markers =False

    def hittest(self, event):
        tol = 10
        for label in self.overlay.labels:
            if abs(label.y + 5 - event.y) < tol and -50 < label.x - event.x < 10:
                return label

    def normal_left_down(self, event):
        self.token = token = self.hittest(event)
        if token:
            self.event_state = 'select'
            token.horizontal_line_visible=True
        else:
            self.event_state = 'normal'

    def select_mouse_move(self, event):
        y=event.y
        self.token.y = y
        self.token.data_y = self.component.value_mapper.map_data(y)

    def select_left_up(self, event):
        self.event_state = 'normal'
        self.token.horizontal_line_visible=False
        self.component.request_redraw()

    def normal_mouse_move(self, event):
        if self.hittest(event):
            event.window.set_pointer('hand')
        else:
            event.window.set_pointer('arrow')

    def normal_left_dclick(self, event):
        x,y=event.x, event.y
        text =self.text
        # if self.label_with_intensity:
        #     text = '{:0.4f}'.format(self.component.value_mapper.map_data(y))

        m = self.overlay.add_marker(x, y, text,
                                    vertical_marker=self.use_vertical_markers,
                                    label_with_intensity=self.label_with_intensity)

        l = self.underlay.add_marker_line(event.x)

        m.on_trait_change(l.set_visible, 'visible')
        m.on_trait_change(l.set_x, 'x')

        self.marker_added = m
        self.component.invalidate_and_redraw()

# ============= EOF =============================================
