# ===============================================================================
# Copyright 2019 ross
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
from chaco.scatterplot import render_markers
from numpy import array

from pychron.core.helpers.color_generators import color1f_generator
from pychron.core.helpers.iterfuncs import groupby_key


class GroupingScatterOverlay(AbstractOverlay):
    def overlay(self, other_component, gc, view_bounds=None, mode='normal'):

        ans = self.analyses
        if any((a.secondary_group_id for a in ans)):
            cgen = color1f_generator()
            points = array(self.component.get_screen_points())
            marker = self.component.marker
            marker_size = self.component.marker_size+0.5
            line_width = self.component.line_width

            for gid, ais in groupby_key(enumerate(ans), lambda x: x[1].secondary_group_id):
                color = next(cgen)
                outline_color = color
                idxs, _ = zip(*ais)
                render_markers(gc, points[idxs, :], marker, marker_size, color, line_width, outline_color)
# ============= EOF =============================================
