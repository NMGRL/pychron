# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import Enum, Bool, Float, on_trait_change
from chaco.api import AbstractOverlay
from enable.colors import color_table
# ============= standard library imports ========================
from numpy import column_stack
# ============= local library imports  ==========================


class ErrorBarOverlay(AbstractOverlay):
    orientation = Enum('x', 'y')

    draw_layer = 'underlay'
    nsigma = 1
    use_end_caps = Bool(True)
    line_width = Float(1)
    _cached_points = None
    _cache_valid = False

    def _get_cached_points(self):
        # print 'laa', self.layout_needed, self._layout_needed, self._cache_valid
        pts = self._cached_points
        if pts is None or not self._cache_valid:
            comp = self.component
            x = comp.index.get_data()
            y = comp.value.get_data()

            if self.orientation == 'x':
                y = comp.value_mapper.map_screen(y)
                err = comp.xerror.get_data()

                err *= self.nsigma
                xlow, xhigh = x - err, x + err
                xlow = comp.index_mapper.map_screen(xlow)
                xhigh = comp.index_mapper.map_screen(xhigh)

                start, end = column_stack((xlow, y)), column_stack((xhigh, y))
                lstart, lend = column_stack((xlow, y - 5)), column_stack((xlow, y + 5))
                ustart, uend = column_stack((xhigh, y - 5)), column_stack((xhigh, y + 5))

            else:
                x = comp.index_mapper.map_screen(x)
                err = comp.yerror.get_data()
                # print 'fff', len(x), len(err), comp.color
                err *= self.nsigma
                ylow, yhigh = y - err, y + err
                ylow = comp.value_mapper.map_screen(ylow)
                yhigh = comp.value_mapper.map_screen(yhigh)
                # idx = arange(len(x))
                start, end = column_stack((x, ylow)), column_stack((x, yhigh))
                lstart, lend = column_stack((x - 5, ylow)), column_stack((x + 5, ylow))
                ustart, uend = column_stack((x - 5, yhigh)), column_stack((x + 5, yhigh))

            pts = start, end, lstart, lend, ustart, uend
            self._cached_points = pts
            self._cache_valid = True

        return pts

    def overlay(self, component, gc, view_bounds, mode='normal'):
        with gc:
            gc.clip_to_rect(component.x, component.y,
                            component.width, component.height)
            # draw normal
            color = component.color
            if isinstance(color, str):
                color = color_table[color]
                # print 'ebo color',color

            gc.set_line_width(self.line_width)
            gc.set_stroke_color(color)
            gc.set_fill_color(color)

            start, end, lstart, lend, ustart, uend = self._get_cached_points()
            gc.line_set(start, end)

            if self.use_end_caps:
                gc.line_set(lstart, lend)
                gc.line_set(ustart, uend)

            gc.draw_path()

    @on_trait_change('component:bounds')
    def _handle_component_change(self, name, new):
        self._cache_valid = False
        self.invalidate_and_redraw()

# ============= EOF =====================================
