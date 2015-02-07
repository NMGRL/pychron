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
from chaco.array_plot_data import ArrayPlotData
from chaco.lineplot import LinePlot
from chaco.plot import Plot
from chaco.plot_containers import VPlotContainer
from chaco.scatterplot import ScatterPlot
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.processing.plotters.base_inset import BaseInset

GOLDEN_RATIO = 1.618


class BaseIdeogramInset(BaseInset):
    def set_limits(self):
        l, h = self.value.get_bounds()
        self.value_range.low = 0
        self.value_range.high = h + 1

        l, h = self.index.get_bounds()
        pad = (h - l) * 0.1
        self.index_range.low -= pad
        self.index_range.high += pad


class IdeogramInset(BaseIdeogramInset, LinePlot):
    def __init__(self, *args, **kw):
        self.border_visible = kw.get('border_visible', True)
        BaseInset.__init__(self, *args, **kw)
        LinePlot.__init__(self)

        self.y_axis.trait_set(tick_label_formatter=lambda x: '',
                              tick_visible=False)
        self.set_limits()


class IdeogramPointsInset(BaseIdeogramInset, ScatterPlot):
    def __init__(self, *args, **kw):
        BaseInset.__init__(self, *args, **kw)
        ScatterPlot.__init__(self)

        self.border_visible = kw.get('border_visible', True)
        self.marker = 'circle'
        # self.color = 'red'
        self.marker_size = 1.5
        if not self.visible_axes:
            self.x_axis.visible = False
            self.y_axis.visible = False

        self.set_limits()

        nsigma = 1
        orientation = 'x'
        line_width = 1
        visible = True
        ebo = ErrorBarOverlay(component=self,
                              orientation=orientation,
                              nsigma=nsigma,
                              line_width=line_width,
                              use_end_caps=False,
                              visible=visible)
        self.overlays.append(ebo)

# ============= EOF =============================================

