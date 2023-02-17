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

from chaco.api import AbstractOverlay
from enable.colors import color_table, QtGui

# ============= standard library imports ========================
from numpy import column_stack
from traits.api import Enum, Bool, Float, on_trait_change


# ============= local library imports  ==========================


class ErrorBarOverlay(AbstractOverlay):
    orientation = Enum("x", "y")
    use_component = True
    draw_layer = "underlay"
    nsigma = 1
    use_end_caps = Bool(True)
    line_width = Float(1)
    _cached_points = None
    _cache_valid = False

    index = None
    value = None
    error = None
    data_orientation = "x"

    def _get_cached_points(self):
        pts = self._cached_points
        if pts is None or not self._cache_valid:
            comp = self.component

            if not self.use_component:
                x = self.index
                y = self.value
            else:
                x = comp.index.get_data()
                y = comp.value.get_data()

            if self.orientation == "x":
                err = self.error
                if self.use_component:
                    err = comp.xerror.get_data()

                if err is not None:
                    scaled_err = err * self.nsigma
                    # print(xlow, y)
                    if self.data_orientation == "x":
                        y = comp.value_mapper.map_screen(y)
                        xlow, xhigh = x - scaled_err, x + scaled_err
                        xlow = comp.index_mapper.map_screen(xlow)
                        xhigh = comp.index_mapper.map_screen(xhigh)
                        start, end = column_stack((xlow, y)), column_stack((xhigh, y))
                        lstart, lend = column_stack((xlow, y - 5)), column_stack(
                            (xlow, y + 5)
                        )
                        ustart, uend = column_stack((xhigh, y - 5)), column_stack(
                            (xhigh, y + 5)
                        )

                    else:
                        x = comp.index_mapper.map_screen(x)
                        ylow, yhigh = y - scaled_err, y + scaled_err
                        ylow = comp.value_mapper.map_screen(ylow)
                        yhigh = comp.value_mapper.map_screen(yhigh)
                        start, end = column_stack((ylow, x)), column_stack((yhigh, x))
                        lstart, lend = column_stack((ylow, x - 5)), column_stack(
                            (ylow, x + 5)
                        )
                        ustart, uend = column_stack((yhigh, x - 5)), column_stack(
                            (yhigh, x + 5)
                        )

                    pts = start, end, lstart, lend, ustart, uend

            else:
                x = comp.index_mapper.map_screen(x)

                err = self.error
                if self.use_component:
                    err = comp.yerror.get_data()

                if err is not None:
                    scaled_err = err * self.nsigma
                    ylow, yhigh = y - scaled_err, y + scaled_err
                    ylow = comp.value_mapper.map_screen(ylow)
                    yhigh = comp.value_mapper.map_screen(yhigh)

                    start, end = column_stack((x, ylow)), column_stack((x, yhigh))
                    lstart, lend = column_stack((x - 5, ylow)), column_stack(
                        (x + 5, ylow)
                    )
                    ustart, uend = column_stack((x - 5, yhigh)), column_stack(
                        (x + 5, yhigh)
                    )

                    pts = start, end, lstart, lend, ustart, uend
            self._cached_points = pts
            self._cache_valid = True

        return pts

    def overlay(self, component, gc, view_bounds, mode="normal"):
        with gc:
            pts = self._get_cached_points()
            if pts:
                gc.clip_to_rect(
                    component.x, component.y, component.width, component.height
                )
                # draw normal
                color = component.color_
                if isinstance(color, str):
                    color = color_table[color]
                elif isinstance(color, QtGui.QColor):
                    color = (
                        color.red() / 255.0,
                        color.green() / 255.0,
                        color.blue() / 255.0,
                    )

                gc.set_line_width(self.line_width)
                gc.set_stroke_color(color)
                gc.set_fill_color(color)

                start, end, lstart, lend, ustart, uend = pts
                gc.line_set(start, end)

                if self.use_end_caps:
                    gc.line_set(lstart, lend)
                    gc.line_set(ustart, uend)

                gc.draw_path()

    @on_trait_change(
        "component:[bounds, _layout_needed, index_mapper:updated, value_mapper:updated]"
    )
    def _handle_component_change(self, obj, name, new):
        self._cache_valid = False

    def invalidate(self):
        self._cache_valid = False
        self.invalidate_and_redraw()


# ============= EOF =====================================
