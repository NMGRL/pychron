# ===============================================================================
# Copyright 2016 Jake Ross
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
from __future__ import absolute_import

from traitsui.api import View, UItem, Item, HGroup, VGroup, Label, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.options.options import (
    AppearanceSubOptions,
    MainOptions,
    SubOptions,
    checkbox_column,
    object_column,
)
from pychron.pychron_constants import APPEARANCE, MAIN


class XYScatterAppearanceOptions(AppearanceSubOptions):
    pass


class XYScatterSubOptions(SubOptions):
    def traits_view(self):
        v = View(Item("show_statistics"))
        return v


class XYScatterMainOptions(MainOptions):
    def _get_columns(self):
        cols = [
            checkbox_column(name="plot_enabled", label="Use"),
            object_column(name="name", width=130, editor=EnumEditor(name="names")),
            object_column(name="fit", editor=EnumEditor(name="fit_types")),
            object_column(name="scale"),
            object_column(name="height", format_func=lambda x: str(x) if x else ""),
            checkbox_column(name="show_labels", label="Labels"),
            checkbox_column(name="x_error", label="X Err."),
            checkbox_column(name="y_error", label="Y Err."),
            checkbox_column(name="ytick_visible", label="Y Tick"),
            checkbox_column(name="ytitle_visible", label="Y Title"),
            checkbox_column(name="y_axis_right", label="Y Right"),
            object_column(
                name="scalar",
                label="Multiplier",
                format_func=lambda x: floatfmt(x, n=2, s=2, use_scientific=True),
            ),
            checkbox_column(name="has_filter", label="Filter", editable=False),
            # object_column(name='filter_str', label='Filter')
        ]

        return cols

    def _get_edit_view(self):
        xr = HGroup(
            Item("x_n", editor=EnumEditor(name="available_names"), label="X"),
            Label("/"),
            UItem("x_d", editor=EnumEditor(name="available_names")),
        )
        yr = HGroup(
            Item("y_n", editor=EnumEditor(name="available_names"), label="Y"),
            Label("/"),
            UItem("y_d", editor=EnumEditor(name="available_names")),
        )
        xs = HGroup(Item("x_key", editor=EnumEditor(name="available_names")))
        ys = HGroup(Item("y_key", editor=EnumEditor(name="available_names")))
        sg = VGroup(xs, ys, visible_when='name=="Scatter"')
        rg = VGroup(xr, yr, visible_when='name=="Ratio"')
        v = View(VGroup(Item("name", editor=EnumEditor(name="names")), rg, sg))
        return v


VIEWS = {
    MAIN.lower(): XYScatterMainOptions,
    "options": XYScatterSubOptions,
    APPEARANCE.lower(): XYScatterAppearanceOptions,
}

# ============= EOF =============================================
