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
from traits.api import HasTraits, Int, Bool, Color, Button, Range
# ============= standard library imports ========================
# ============= local library imports  ==========================


class BaseGroupOptions(HasTraits):
    group_id = Int
    color = Color
    alpha = Range(0, 100, 70)
    use_fill = Bool(True)
    line_color = Color
    line_width = Int(1)

    bind_colors = Bool(True)
    edit_button = Button

    def _color_changed(self):
        if self.bind_colors:
            self.line_color = self.color

    def _line_color_changed(self):
        if self.bind_colors:
            self.color = self.line_color

    def _bind_colors_changed(self, new):
        if new:
            self.line_color = self.color

# ============= EOF =============================================
