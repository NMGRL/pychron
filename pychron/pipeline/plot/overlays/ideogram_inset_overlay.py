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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import

from chaco.api import LinePlot
from chaco.api import ScatterPlot

from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.pipeline.plot.overlays.base_inset import BaseInset

GOLDEN_RATIO = 1.618


class BaseIdeogramInset(BaseInset):
    # def set_limits(self):
    #     l, h = self.value.get_bounds()
    #     self.value_range.low = 0
    #     self.value_range.high = h + 1

    # l, h = self.index.get_bounds()
    # pad = (h - l) * 0.1
    # self.index_range.low -= pad
    # self.index_range.high += pad
    def set_y_limits(self, y1, y2):
        self.value_range.low = y1
        self.value_range.high = y2

    def get_y_limits(self):
        v = self.value_range
        return v.low, v.high

    def set_x_limits(self, x1, x2):
        self.index_range.low = x1
        self.index_range.high = x2

    def get_x_limits(self):
        r = self.index_range
        return r.low, r.high


try:

    class IdeogramInset(BaseIdeogramInset, LinePlot):
        def __init__(self, *args, **kw):
            self.border_visible = kw.get("border_visible", True)
            BaseInset.__init__(self, *args, **kw)
            LinePlot.__init__(self)

            self.y_axis.trait_set(tick_label_formatter=lambda x: "", tick_visible=False)
            # self.set_limits()

except TypeError:
    # documentation auto doc hack
    class IdeogramInset:
        pass


try:

    class IdeogramPointsInset(BaseIdeogramInset, ScatterPlot):
        def __init__(self, *args, **kw):
            BaseInset.__init__(self, *args, **kw)
            ScatterPlot.__init__(self)

            self.border_visible = kw.get("border_visible", True)
            self.marker = "circle"
            # self.color = 'red'
            self.marker_size = 1.5
            if not self.visible_axes:
                self.x_axis.visible = False
                self.y_axis.visible = False

            # self.set_limits()

            nsigma = 1
            orientation = "x"
            line_width = 1
            visible = True
            ebo = ErrorBarOverlay(
                component=self,
                orientation=orientation,
                nsigma=nsigma,
                line_width=line_width,
                use_end_caps=False,
                visible=visible,
            )
            self.overlays.append(ebo)

except TypeError:
    # documentation auto doc hack
    class IdeogramPointsInset:
        pass


# ============= EOF =============================================
