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

from enable.markers import MarkerNameDict, marker_names

# ============= enthought library imports =======================
from traits.api import Range, Trait
from traitsui.api import View, UItem, Item, HGroup, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.options.group.base_group_options import BaseGroupOptions
from pychron.pychron_constants import NULL_STR

# Mapping of marker string names to classes.
# MarkerNameDict = {"square": SquareMarker,
#                   "circle": CircleMarker,
#                   "triangle": TriangleMarker,
#                   "inverted_triangle": Inverted_TriangleMarker,
#                   "left_triangle":LeftTriangleMarker,
#                   "right_triangle": RightTriangleMarker,
#                   "pentagon": PentagonMarker,
#                   "hexagon": Hexagon1Marker,
#                   "hexagon2": Hexagon2Marker,
#                   "plus": PlusMarker,
#                   "cross": CrossMarker,
#                   "star": StarMarker,
#                   "cross_plus": CrossPlusMarker,
#                   "diamond": DiamondMarker,
#                   "dot": DotMarker,
#                   "pixel": PixelMarker,
#                   "custom": CustomMarker}

m = [NULL_STR] + list(marker_names)
md = MarkerNameDict.copy()
md[NULL_STR] = ""

# A mapped trait that allows string naming of marker classes.
MarkerTrait = Trait("circle", md, editor=EnumEditor(values=m))


class IdeogramGroupOptions(BaseGroupOptions):
    marker_size = Range(0.0, 10.0, 1.0, mode="spinner")
    marker = MarkerTrait

    def marker_non_default(self):
        return self.marker != NULL_STR

    def marker_size_non_default(self):
        return self.marker_size != 1

    def traits_view(self):
        fill_grp = BorderVGroup(
            HGroup(UItem("use_fill"), UItem("color")),
            Item("alpha", label="Opacity"),
            label="Fill",
        )

        line_grp = BorderVGroup(
            UItem("line_color"), Item("line_width", label="Width"), label="Line"
        )

        mgrp = BorderHGroup(UItem("marker"), UItem("marker_size"), label="Marker")

        g = BorderVGroup(
            Item(
                "bind_colors",
                label="Bind Colors",
                tooltip="Bind the Fill and Line colors, i.e changing the Fill color changes"
                "the line color and vice versa",
            ),
            HGroup(fill_grp, line_grp, mgrp),
            label="Group {}".format(self.group_id + 1),
        )
        v = View(g)
        return v


# ============= EOF =============================================
