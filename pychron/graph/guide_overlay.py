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
from enable.colors import ColorTrait
from enable.enable_traits import LineStyle
from traits.api import Enum, Float
from chaco.api import AbstractOverlay

# =============standard library imports ========================

# =============local library imports  ==========================


class GuideOverlay(AbstractOverlay):
    """
    draws a horizontal or vertical line at the specified value
    """
    orientation = Enum('h', 'v')
    value = Float
    color = ColorTrait("red")
    line_style = LineStyle('dash')

    line_width = Float(1)

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        """

        """
        with gc:
            gc.clip_to_rect(self.component.x, self.component.y, self.component.width, self.component.height)
            gc.set_line_dash(self.line_style_)
            gc.set_line_width(self.line_width)
            gc.set_stroke_color(self.color_)
            gc.begin_path()

            if self.orientation == 'h':
                x1 = self.component.x
                x2 = self.component.x2
                y1 = y2 = self.component.value_mapper.map_screen(self.value)

            else:
                y1 = self.component.y
                y2 = self.component.y2
                x1 = x2 = self.component.index_mapper.map_screen(self.value)

            gc.move_to(x1, y1)
            gc.line_to(x2, y2)
            gc.stroke_path()

# ============= EOF =====================================
