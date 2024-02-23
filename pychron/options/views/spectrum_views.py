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

from traitsui.api import View, UItem, Item, HGroup, VGroup, Group, EnumEditor

from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options import (
    SubOptions,
    AppearanceSubOptions,
    GroupSubOptions,
    checkbox_column,
    object_column,
    MainOptions,
    TitleSubOptions,
)
from pychron.pychron_constants import (
    MAIN,
    APPEARANCE,
    FLECK_PLATEAU_DEFINITION,
    MAHON_PLATEAU_DEFINITION,
    SPECTRUM,
    PLATEAU,
    GROUPS,
    DISPLAY,
)


class SpectrumSubOptions(SubOptions):
    def traits_view(self):
        tooltip = """---= No weighted. Isotopic Recombination and quadratic summing 
of uncertainties
Variance=  Inverse variance weighting
Volume=  Weight by signal size.  Wi = (Vi*Ei)**2  where Vi = Ar39i/TotalAr39 and Ei=1 sigma uncertainty in Ar40/Ar39)
"""
        integrated_grp = BorderVGroup(
            Item("integrated_age_weighting", tooltip=tooltip, label="Weighting"),
            Item("integrated_include_omitted", label="Include Omitted"),
            Item("include_j_error_in_integrated", label="Include J Error"),
            label="Integrated Age",
        )
        iso_grp = BorderHGroup(
            Item(
                "use_isochron_trapped",
                tooltip="Use the (40/36)trapped calculated from an inverse isochron instead of "
                "the nominal (40/36)atm set in Preferences/Constants/Ratios",
                label="Use Isochron",
            ),
            Item(
                "include_isochron_trapped_error",
                tooltip="Propagate the (40/36)trapped uncertainty",
                label="Include Uncertainty",
            ),
            label="Trapped Ar40/Ar36",
        )
        tgrp = BorderVGroup(
            Item(
                "omit_by_tag",
                label="Omit Tags",
                tooltip='If selected only analyses tagged as "OK" are included in the calculations',
            ),
            label="Tags",
        )

        return self._make_view(VGroup(integrated_grp, iso_grp, tgrp))


class SpectrumAppearance(AppearanceSubOptions):
    def traits_view(self):
        ee = HGroup(
            Item("error_info_fontname", label="Error Info"),
            UItem("error_info_fontsize"),
        )

        ll = HGroup(Item("label_fontname", label="Labels"), UItem("label_fontsize"))

        pp = HGroup(
            Item("plateau_fontname", label="Plateau"), UItem("plateau_fontsize")
        )
        ii = HGroup(
            Item("integrated_fontname", label="Integrated"),
            UItem("integrated_fontsize"),
        )

        fgrp = VGroup(
            UItem("fontname"),
            ee,
            ll,
            pp,
            ii,
            HGroup(self._get_xfont_group(), self._get_yfont_group()),
            label="Fonts",
            show_border=True,
        )

        g = VGroup(
            self._get_bg_group(),
            self._get_layout_group(),
            self._get_padding_group(),
            self._get_margin_group(),
            self._get_grid_group(),
        )
        return self._make_view(VGroup(g, fgrp))


class DisplaySubOptions(TitleSubOptions):
    def traits_view(self):
        title_grp = self._get_title_group()

        gen_grp = HGroup(
            Item("show_info", tooltip="Show general info in the upper right corner"),
            show_border=True,
            label="General",
        )

        legend_grp = VGroup(
            Item("include_legend", label="Show"),
            Item("include_sample_in_legend", label="Include Sample"),
            Item("legend_location", label="Location"),
            label="Legend",
            show_border=True,
        )

        label_grp = HGroup(
            Item("display_step", label="Step"),
            Item("display_extract_value", label="Power/Temp"),
            # spring,
            # Item('step_label_font_size', label='Size'),
            show_border=True,
            label="Labels",
        )

        mswd = HGroup(
            Item("include_age_mswd", label="Display MSWD"),
            Item(
                "mswd_sig_figs", label="MSWD SigFIgs", enabled_when="include_age_mswd"
            ),
        )
        n = HGroup(Item("include_age_n", label="Display N"))
        age_grp = VGroup(
            Item("nsigma", tooltip="NSigma to display for Plateau and Integrated ages"),
            mswd,
            n,
            show_border=True,
            label="Age Info",
        )

        mswd = HGroup(
            Item("include_plateau_mswd", label="Display MSWD"),
            Item(
                "plateau_mswd_sig_figs",
                label="MSWD SigFIgs",
                enabled_when="include_age_mswd",
            ),
        )
        n = HGroup(Item("include_plateau_n", label="Display N"))

        plat_grp = VGroup(
            HGroup(
                UItem("display_plateau_info", tooltip="Display plateau info"),
                # Item('plateau_font_size', label='Size',
                #      enabled_when='display_plateau_info'),
                Item("plateau_sig_figs", label="SigFigs"),
            ),
            HGroup(
                Item(
                    "include_plateau_sample",
                    tooltip="Add the Sample name to the Plateau indicator",
                    label="Sample",
                ),
                Item(
                    "include_plateau_identifier",
                    tooltip="Add the Identifier to the Plateau indicator",
                    label="Identifier",
                ),
            ),
            Item("plateau_arrow_visible"),
            Item("dim_non_plateau", label="Dim Non Plateau"),
            mswd,
            n,
            show_border=True,
            label="Plateau",
        )

        integrated_grp = HGroup(
            UItem("display_integrated_info", tooltip="Display integrated age info"),
            # Item('integrated_font_size', label='Size',
            #      enabled_when='display_integrated_info'),
            Item("integrated_sig_figs", label="SigFigs"),
            show_border=True,
            label="Integrated",
        )

        weighted_mean_grp = HGroup(
            UItem("display_weighted_mean_info", tooltip="Display weighted age info"),
            Item("weighted_mean_sig_figs", label="SigFigs"),
            Item(
                "display_weighted_bar",
                label="Display Weighted Mean Bar",
                tooltip="Display weighted mean age if no plateau",
            ),
            show_border=True,
            label="Weighted Mean",
        )

        display_grp = Group(
            gen_grp,
            age_grp,
            legend_grp,
            title_grp,
            label_grp,
            plat_grp,
            HGroup(integrated_grp, weighted_mean_grp),
            show_border=True,
            label="Display",
        )

        return self._make_view(display_grp)


class CalculationSubOptions(SubOptions):
    def traits_view(self):
        lgrp = VGroup(
            Item(
                "plateau_method",
                tooltip="Fleck 1977={}\n"
                "Mahon 1996={}".format(
                    FLECK_PLATEAU_DEFINITION, MAHON_PLATEAU_DEFINITION
                ),
                label="Method",
            ),
            Item("plateau_age_error_kind", width=-100, label="Error Type"),
            Item(
                "include_j_error_in_plateau",
                tooltip="Include J error in plateau age",
                label="Include J Error",
            ),
            Item("include_decay_error", label="Include Decay Error"),
        )
        rgrp = VGroup(
            Item("extend_plateau_end_caps", label="Extend End Caps"),
            icon_button_editor(
                "edit_plateau_criteria", "cog", tooltip="Edit Plateau Criteria"
            ),
        )
        plat_grp = HGroup(lgrp, rgrp)

        error_grp = BorderVGroup(
            HGroup(
                Item(
                    "step_nsigma",
                    editor=EnumEditor(values=[1, 2, 3]),
                    tooltip="Set the size of the error envelope in standard deviations",
                    label="N. Sigma",
                )
            ),
            label="Error Envelope",
        )

        return self._make_view(VGroup(plat_grp, error_grp))


class SpectrumMainOptions(MainOptions):
    def _get_columns(self):
        cols = [
            checkbox_column(name="plot_enabled", label="Use"),
            object_column(name="name", editor=EnumEditor(name="names")),
            object_column(name="scale"),
            object_column(name="height", format_func=lambda x: str(x) if x else ""),
            checkbox_column(name="show_labels", label="Labels"),
            checkbox_column(name="y_error", label="Y Err."),
            checkbox_column(name="ytick_visible", label="Y Tick"),
            checkbox_column(name="ytitle_visible", label="Y Title"),
            checkbox_column(name="y_axis_right", label="Y Right"),
            # object_column(name='filter_str', label='Filter')
        ]

        return cols

    def _get_edit_view(self):
        v = View(
            BorderVGroup(
                self._get_name_grp(), self._get_yticks_grp(), self._get_ylimits_group()
            )
        )
        return v


VIEWS = {
    MAIN.lower(): SpectrumMainOptions,
    SPECTRUM.lower(): SpectrumSubOptions,
    APPEARANCE.lower(): SpectrumAppearance,
    PLATEAU.lower(): CalculationSubOptions,
    DISPLAY.lower(): DisplaySubOptions,
    GROUPS.lower(): GroupSubOptions,
}

# ============= EOF =============================================
