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

# ============= enthought library imports =======================
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor, Label

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderVGroup
from pychron.options.options import (
    SubOptions,
    AppearanceSubOptions,
    object_column,
    checkbox_column,
)
from pychron.options.views.ratio_series_views import RatioSeriesMainOptions
from pychron.pychron_constants import MAIN, APPEARANCE


class ICFactorMainOptions(RatioSeriesMainOptions):
    def _get_ic_group(self):
        return BorderVGroup(
            HGroup(
                UItem("numerator", editor=EnumEditor(name="detectors")),
                Label("/"),
                UItem("denominator", editor=EnumEditor(name="detectors")),
            ),
            HGroup(
                Item("fit", editor=EnumEditor(name="fit_types")),
                UItem("error_type", editor=EnumEditor(name="error_types")),
            ),
            Item("analysis_type", editor=EnumEditor(name="analysis_types")),
            Item("standard_ratio"),
            label="IC",
        )

    def _get_columns(self):
        return [
            object_column(name="numerator", editor=EnumEditor(name="detectors")),
            object_column(name="denominator", editor=EnumEditor(name="detectors")),
            checkbox_column(name="plot_enabled", label="Plot"),
            checkbox_column(name="save_enabled", label="Save"),
            object_column(name="standard_ratio", label="Standard Ratio"),
            object_column(name="fit", editor=EnumEditor(name="fit_types"), width=75),
            object_column(
                name="error_type",
                editor=EnumEditor(name="error_types"),
                width=75,
                label="Error",
            ),
            object_column(name="height", label="Height"),
        ]


class ICFactorSubOptions(SubOptions):
    def traits_view(self):
        src = BorderVGroup(
            Item("use_source_correction", label="Use Source Correction"),
            Item("source_correction_kind", label="Kind"),
            label="Source",
        )

        disc = BorderVGroup(
            Item("use_discrimination", label="Use Discrimination"),
            label="Discrimination",
        )

        v = View(
            VGroup(
                Item(
                    "delete_existing",
                    label="Delete Existing",
                    tooltip="Delete existing icfactors. Only necessary if you have "
                    "redefined how you are handling the IC factor correction. ",
                ),
                Item("show_statistics"),
                Item("show_current"),
                Item(
                    "link_plots",
                    label="Link Plots",
                    tooltip="Link plots together so that omitting an "
                    "analysis from any plot omits the analysis on "
                    "all other plots",
                ),
                src,
                disc,
            )
        )
        return v


class ICFactorAppearance(AppearanceSubOptions):
    pass


# ===============================================================
# ===============================================================
VIEWS = {
    MAIN.lower(): ICFactorMainOptions,
    "icfactor": ICFactorSubOptions,
    APPEARANCE.lower(): ICFactorAppearance,
}

# ============= EOF =============================================
