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
from traitsui.api import UItem, Item, HGroup, VGroup, Group, EnumEditor, spring, View

from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options import (
    SubOptions,
    AppearanceSubOptions,
    GroupSubOptions,
    MainOptions,
    TitleSubOptions,
    GuidesOptions,
)
from pychron.processing.j_error_mixin import J_ERROR_GROUP
from pychron.pychron_constants import (
    MAIN,
    APPEARANCE,
    SCHAEN2020_3,
    SCHAEN2020_3youngest,
    GROUPS,
    GUIDES,
)


class DisplaySubOptions(TitleSubOptions):
    def traits_view(self):
        errbar_grp = VGroup(
            HGroup(
                Item("x_end_caps", label="X End Caps"),
                Item("y_end_caps", label="Y End Caps"),
            ),
            HGroup(
                Item("error_bar_line_width", label="Line Width"),
                Item("error_bar_nsigma", label="NSigma"),
            ),
            show_border=True,
            label="Error Bars",
        )

        an_grp = VGroup(
            Item("analysis_number_sorting", label="Analysis# Order"),
            Item(
                "global_analysis_number_sorting",
                label="Global Sort",
                tooltip="Applicable only when " "using Aux Grouping",
            ),
            HGroup(
                Item("include_group_legend", label="Include Group Legend"),
                UItem(
                    "group_legend_label_attribute", enabled_when="include_group_legend"
                ),
            ),
            HGroup(
                Item("use_cmap_analysis_number", label="Use Color Mapping"),
                UItem("cmap_analysis_number", enabled_when="use_cmap_analysis_number"),
            ),
            Item("use_latest_overlay"),
            show_border=True,
            label="Analysis #",
        )

        label_grp = VGroup(
            HGroup(
                Item("label_box"),
                Item(
                    "analysis_label_display",
                    label="Label Format",
                    width=100,
                    style="readonly",
                ),
                spring,
                icon_button_editor(
                    "edit_label_format_button", "cog", tooltip="Open Label maker"
                ),
            ),
            VGroup(
                Item(
                    "label_all_peaks",
                    label="Label Peaks",
                    tooltip="Label each peak with its calculated age",
                ),
                HGroup(
                    Item("peak_label_bgcolor_enabled", label="Background"),
                    UItem(
                        "peak_label_bgcolor", enabled_when="peak_label_bgcolor_enabled"
                    ),
                ),
                HGroup(
                    Item(
                        "peak_label_border",
                        label="Border Width",
                        tooltip="Border width in pixels, user 0 to disable",
                    ),
                    Item("peak_label_border_color", label="Border"),
                    enabled_when="peak_label_border",
                ),
                Item("peak_label_sigfigs", label="SigFigs"),
                show_border=True,
                label="Peaks",
            ),
            show_border=True,
            label="Label",
        )

        inset_grp = VGroup(
            HGroup(
                Item("display_inset", label="Use"),
                Item("inset_location", label="Location"),
                Item("inset_width", label="Width"),
                Item("inset_height", label="Height"),
            ),
            show_border=True,
            label="Inset",
        )

        mean_label = HGroup(
            Item(
                "mean_label_display",
                label="Mean Label Format",
                width=100,
                style="readonly",
            ),
            spring,
            icon_button_editor(
                "edit_mean_format_button", "cog", tooltip="Open Mean Label maker"
            ),
        )

        submean = HGroup(
            VGroup(Item("display_group_marker", label="Group Marker")),
            VGroup(
                Item(
                    "display_mean",
                    label="Value",
                ),
                Item(
                    "display_percent_error",
                    label="%Error",
                ),
            ),
            VGroup(
                Item(
                    "display_mean_mswd",
                    label="MSWD",
                ),
                Item("display_mean_n", label="N"),
                Item("display_mswd_pvalue", label="P-Value"),
            ),
            VGroup(
                Item("mean_sig_figs", label="Mean SigFigs"),
                Item("mswd_sig_figs", label="MSWD SigFigs"),
            ),
            enabled_when="display_mean_indicator",
        )

        mean_grp = VGroup(
            Item("display_mean_indicator", label="Indicator"),
            submean,
            mean_label,
            show_border=True,
            label="Mean",
        )

        info_grp = HGroup(
            Item("show_info", label="Show"),
            Item("show_mean_info", label="Mean", enabled_when="show_info"),
            Item("show_error_type_info", label="Error Type", enabled_when="show_info"),
            show_border=True,
            label="Info",
        )

        display_grp = VGroup(
            mean_grp,
            an_grp,
            inset_grp,
            self._get_title_group(),
            label_grp,
            info_grp,
            errbar_grp,
            scrollable=True,
            show_border=True,
            label="Display",
        )

        return self._make_view(display_grp)


class CalculationSubOptions(SubOptions):
    def traits_view(self):
        calcgrp = BorderVGroup(
            Item(
                "probability_curve_kind", width=-150, label="Probability Curve Method"
            ),
            Item("mean_calculation_kind", width=-150, label="Mean Calculation Method"),
            BorderVGroup(
                Item("shapiro_wilk_alpha", label="Shapiro-Wilk alpha"),
                HGroup(
                    Item("skew_min", label="Skew Min."),
                    Item("skew_max", label="Skew Max"),
                ),
                visible_when='mean_calculation_kind =="{}" '
                'or mean_calculation_kind=="{}"'.format(
                    SCHAEN2020_3, SCHAEN2020_3youngest
                ),
                label="Normality Options",
            ),
            Item("error_calc_method", width=-150, label="Error Calculation Method"),
            Item("nsigma", label="Age Error NSigma"),
            BorderVGroup(
                J_ERROR_GROUP,
                BorderHGroup(
                    Item("include_irradiation_error"), Item("include_decay_error")
                ),
                label="Uncertainty",
            ),
            label="Calculations",
        )

        return self._make_view(calcgrp)


class IdeogramSubOptions(SubOptions):
    def traits_view(self):
        xgrp = VGroup(
            Item("index_attr", editor=EnumEditor(name="index_attrs"), label="X Value"),
            HGroup(
                Item("age_normalize", label="Normalize Age"),
                UItem("age_normalize_value"),
            ),
            Item(
                "reverse_x_axis",
                label="Reverse",
                tooltip="Display decreasing left to right",
            ),
            HGroup(
                UItem("use_static_limits"),
                Item("xlow", label="Min.", enabled_when="object.use_static_limits"),
                Item("xhigh", label="Max.", enabled_when="object.use_static_limits"),
                show_border=True,
                label="Static Limits",
            ),
            HGroup(
                UItem("use_asymptotic_limits"),
                # Item('asymptotic_width', label='% Width',
                #      tooltip='Width of asymptotic section that is less than the Asymptotic %'),
                Item(
                    "asymptotic_height_percent",
                    tooltip="Percent of Max probability",
                    label="% Height",
                ),
                # icon_button_editor('refresh_asymptotic_button', 'refresh',
                #                    enabled_when='object.use_asymptotic_limits',
                #                    tooltip='Refresh plot with defined asymptotic limits'),
                enabled_when="not object.use_centered_range and not object.use_static_limits",
                show_border=True,
                label="Asymptotic Limits",
            ),
            HGroup(
                UItem("use_centered_range"),
                UItem("centered_range", enabled_when="object.use_centered_range"),
                label="Center on fixed range",
                show_border=True,
                enabled_when="not object.use_static_limits",
            ),
            HGroup(
                UItem("use_xpad"),
                Item("xpad", label="Pad", enabled_when="use_xpad"),
                Item(
                    "xpad_as_percent",
                    tooltip="Treat Pad as a percent of the nominal width, otherwise Pad is in Ma. "
                    "e.g if width=10 Ma, Pad=0.5 "
                    "the final width will be 10 + (10*0.5)*2 = 20 Ma.",
                    enabled_when="use_xpad",
                    label="%",
                ),
                label="X Pad",
                show_border=True,
            ),
            show_border=True,
            label="X",
        )

        tgrp = BorderVGroup(
            Item(
                "omit_by_tag",
                label="Omit Tags",
                tooltip='If selected only analyses tagged as "OK" are included in the calculations',
            ),
            label="Tags",
        )

        rtgrp = BorderVGroup(
            Item(
                "show_results_table",
                label="Show Summary",
                tooltip="Display a summary table below the ideogram",
            ),
            Item("show_ttest_table", label="Show T-test"),
            Item("show_rvalues", label="Show R Values"),
            label="Aux. Tables",
        )

        cgrp = BorderVGroup(Item("show_correlation_ellipses"), label="Correlation")
        return self._make_view(VGroup(xgrp, tgrp, rtgrp, cgrp))


class IdeogramAppearance(AppearanceSubOptions):
    def traits_view(self):
        mi = BorderVGroup(
            HGroup(UItem("mean_indicator_fontname"), UItem("mean_indicator_fontsize")),
            Item("display_mean_location", label="Location"),
            label="Mean Indicator",
        )

        ee = BorderHGroup(
            UItem("error_info_fontname"),
            UItem("error_info_fontsize"),
            label="Error Info",
        )

        ll = BorderHGroup(
            UItem("label_fontname"), UItem("label_fontsize"), label="Labels"
        )

        fgrp = BorderVGroup(
            BorderHGroup(UItem("fontname"), label="Change All"),
            HGroup(mi, ee),
            ll,
            HGroup(self._get_xfont_group(), self._get_yfont_group()),
            label="Fonts",
        )

        subgroup = BorderVGroup(Item("show_subgroup_indicators"), label="Subgroup")

        g = VGroup(
            subgroup,
            self._get_nominal_group(),
            self._get_layout_group(),
            self._get_margin_group(),
            self._get_padding_group(),
            fgrp,
        )
        return self._make_view(g)


class IdeogramMainOptions(MainOptions):
    def _get_edit_view(self):
        tooltip = """'Omit analyses based on the provided criteria. For example x>10 will omit any analysis
greater than 10. The value of x depends on the Auxiliary plot e.g. x is age for Analysis Number or K/Ca for KCa.
x is simply a placeholder and can be replaced by any letter or word except for a few exceptions
(i.e and, or, is, on, if, not...). To filter based on error or %error use "error" and "percent_error". Multiple predicates may be combined
with "and", "or". Valid comparators are "<,<=,>,>=,==,!=". "==" means "equals" and "!=" means "not equal".
Additional examples
1. x<10
2. age<10 or age>100
3. age<10 or error>1
4. x<=10 or percent_error>50
5. xyz<=10 and error>=0.1"""
        sigma_tooltip = """Omit analyses greater the N sigma from the arithmetic mean"""

        fgrp = BorderVGroup(
            HGroup(
                Item("filter_str", tooltip=tooltip, label="Filter"),
                UItem("filter_str_tag"),
            ),
            HGroup(
                Item("sigma_filter_n", label="Sigma Filter N", tooltip=sigma_tooltip),
                UItem("sigma_filter_tag"),
            ),
            label="Filtering",
        )

        v = View(
            VGroup(
                self._get_name_grp(),
                self._get_yticks_grp(),
                self._get_ylimits_group(),
                self._get_marker_group(),
                fgrp,
            )
        )
        return v


# ===============================================================
# ===============================================================
VIEWS = {
    MAIN.lower(): IdeogramMainOptions,
    "ideogram": IdeogramSubOptions,
    APPEARANCE.lower(): IdeogramAppearance,
    "calculations": CalculationSubOptions,
    "display": DisplaySubOptions,
    GROUPS.lower(): GroupSubOptions,
    GUIDES.lower(): GuidesOptions,
}

# ===============================================================
# ===============================================================


# ============= EOF =============================================
