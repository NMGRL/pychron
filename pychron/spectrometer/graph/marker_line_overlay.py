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
from chaco.abstract_overlay import AbstractOverlay
from traits.trait_types import List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.spectrometer.graph.marker_line import MarkerLine


class MarkerLineOverlay(AbstractOverlay):
    _cached_lines = List

    def add_marker_line(self, x, bgcolor='black'):
        l = MarkerLine(data_x=self.component.index_mapper.map_data(x),
                       x=x,
                       bgcolor=bgcolor)
        self._cached_lines.append(l)
        self._layout_needed = True
        return l

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(other_component.x, other_component.y,
                            other_component.width,
                            other_component.height)
            gc.set_stroke_color((1, 0, 0, 0.75))
            gc.set_line_dash((12, 6))
            gc.translate_ctm(0, other_component.y)
            for l in self._cached_lines:
                if l.visible:
                    l.draw(gc, other_component.height)

    def _do_layout(self):
        if self._layout_needed:
            mapper = self.component.index_mapper
            for ci in self._cached_lines:
                if ci.visible:
                    ci.x = mapper.map_screen(ci.data_x)
                    ci.height = self.component.height
                    ci.visible = bool(ci.x > 0)

            self._layout_needed = False

# ============= EOF =============================================
