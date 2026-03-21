# ===============================================================================
# Copyright 2021 ross
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

from chaco.abstract_overlay import AbstractOverlay
from chaco.api import render_markers


class SubGroupPointOverlay(AbstractOverlay):
    def overlay(self, oc, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(oc.x, oc.y, oc.x2, oc.y2)

            dd = self.component.index.get_data()
            xs = self.component.index_mapper.map_screen(dd)

            dd = self.component.value.get_data()
            ys = self.component.value_mapper.map_screen(dd)

            points = [p for i, p in enumerate(zip(xs, ys)) if i in self.indexes]

            cmarker = self.component.marker

            marker_size = self.component.marker_size
            color = self.component.color
            line_width = 2
            outline_color = [1.0 - ci for ci in color[:3]]
            render_markers(
                gc, points, cmarker, marker_size, color, line_width, outline_color
            )


# ============= EOF =============================================
