# ===============================================================================
# Copyright 2015 Jake Ross
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
from __future__ import absolute_import
from traits.api import Instance, Tuple, Color, Bool, Any, Float, Property

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.crosshairs_overlay import (
    CrosshairsOverlay,
    SimpleCrosshairsOverlay,
)
from pychron.canvas.canvas2D.map_canvas import MapCanvas

DIRECTIONS = {"Left": ("x", -1), "Right": ("x", 1), "Down": ("y", -1), "Up": ("y", 1)}


class StageCanvas(MapCanvas):
    crosshairs_overlay = Instance(SimpleCrosshairsOverlay)
    crosshairs_color = Color("black")
    crosshairs_line_width = Float(1.0)

    stage_position = Property(depends_on="_stage_position")
    _stage_position = Tuple(Float, Float)

    desired_position = Property(depends_on="_desired_position")
    _desired_position = Any

    show_current_position = Bool(True)
    current_position = Property(depends_on="cur_pos")
    cur_pos = Tuple(Float(0), Float(0))
    show_desired_position = Bool(True)
    desired_position_color = Color("green")

    def get_stage_screen_position(self):
        return self.map_screen([self._stage_position])[0]

    def get_stage_position(self):
        return self._stage_position

    def set_stage_position(self, x, y):
        """ """
        if x is not None and y is not None:
            self._stage_position = (x, y)
            self.invalidate_and_redraw()

    def clear_desired_position(self):
        self._desired_position = None
        self.request_redraw()

    def set_desired_position(self, x, y):
        """ """
        self._desired_position = (x, y)
        self.request_redraw()

    # ===============================================================================
    # interactor
    # ===============================================================================
    def normal_mouse_move(self, event):
        """ """
        self.cur_pos = (event.x, event.y)

        if self.valid_position(event.x, event.y):
            event.window.set_pointer(self.cross_pointer)
        else:
            event.window.set_pointer(self.normal_pointer)

        event.handled = True
        # self.request_redraw()

    def normal_mouse_enter(self, event):
        """ """
        event.window.set_pointer(self.cross_pointer)
        event.handled = True

    def normal_mouse_leave(self, event):
        """ """
        event.window.set_pointer(self.normal_pointer)
        self.request_redraw()
        event.handled = True

    def normal_key_pressed(self, event):
        c = event.character
        if c in ("Left", "Right", "Up", "Down"):
            ax_key, direction = DIRECTIONS[c]
            direction = self._calc_relative_move_direction(c, direction)
            distance = 5 if event.shift_down else 1
            self.stage_manager.relative_move(ax_key, direction, distance)
            event.handled = True
        elif c in ("a", "A"):
            self.stage_manager.accept_point()

    def key_released(self, char):
        """
        called from outside by StageCompnentEditor
        """
        self.stage_manager.key_released()

    # ===============================================================================
    # private
    # ===============================================================================
    def _calc_relative_move_direction(self, char, direction):
        return direction

    def _add_crosshairs(self, klass=None):
        if klass is None:
            klass = CrosshairsOverlay
        ch = klass(component=self)
        self.crosshairs_overlay = ch
        self.overlays.append(ch)

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_current_position(self):
        md = self.map_data(self.cur_pos)
        return self.cur_pos[0], md[0], self.cur_pos[1], md[1]

    def _get_stage_position(self):
        """ """

        return self.map_screen([self._stage_position])[0]

    def _get_desired_position(self):
        """ """

        if self._desired_position is not None:
            x, y = self.map_screen([self._desired_position])[0]
            return x, y


# ============= EOF =============================================
