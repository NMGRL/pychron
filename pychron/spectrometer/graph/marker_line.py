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
from enable.colors import ColorTrait
from traits.has_traits import HasTraits
from traits.trait_types import Float
# ============= standard library imports ========================
# ============= local library imports  ==========================



class MarkerLine(HasTraits):
    x = Float
    height = Float
    visible = True
    bgcolor = ColorTrait

    def draw(self, gc, height):
        with gc:
            gc.set_stroke_color((0, 0, 0, 1))
            gc.move_to(self.x, 0)
            gc.line_to(self.x, height)
            gc.stroke_path()

    def set_visible(self, new):
        self.visible = new

    def set_x(self, new):
        self.x=new
# ============= EOF =============================================
