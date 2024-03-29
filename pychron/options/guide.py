# ===============================================================================
# Copyright 2022 ross
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
from enable.enable_traits import LineStyle
from traits.api import HasTraits, Enum, Float, Color, RGBColor, Str, Range, List, Bool


class Guide(HasTraits):
    orientation = Enum("h", "v")
    value = Float
    alpha = Range(0.0, 1.0, 1.0)
    color = RGBColor("red")
    line_style = LineStyle("dash")
    line_width = Float(1)
    label = Str
    plotname = Str
    plotnames = List
    visible = Bool

    def should_plot(self, plot):
        ret = True
        if not self.plotname == "All Plots":
            if self.plotname:
                ps = list(reversed(self.plotnames))
                ret = ps.index(self.plotname) == plot

        return ret

    def kwargs_keys(self):
        return ("orientation", "color", "line_style", "alpha", "line_width")

    def to_kwargs(self):
        return {attr: getattr(self, attr) for attr in self.kwargs_keys()}


class RangeGuide(Guide):
    minvalue = Float
    maxvalue = Float


# ============= EOF =============================================
