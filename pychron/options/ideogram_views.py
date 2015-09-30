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
from enable.markers import marker_names
from traitsui.api import UItem, Item, HGroup, VGroup, Group, EnumEditor, spring, View
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options import SubOptions, AppearanceSubOptions, GroupSubOptions, MainOptions


class DisplaySubOptions(SubOptions):
    def traits_view(self):
        errbar_grp = VGroup(HGroup(Item('x_end_caps', label='X End Caps'),
                                   Item('y_end_caps', label='Y End Caps'),
                                   Item('error_bar_nsigma', label='NSigma')),
                            show_border=True,
                            label='Error Bars')

        an_grp = VGroup(Item('analysis_number_sorting', label='Analysis# Sort'),
                        HGroup(Item('use_cmap_analysis_number', label='Use Color Mapping'),
                               UItem('cmap_analysis_number', enabled_when='use_cmap_analysis_number')),
                        Item('use_latest_overlay'), show_border=True, label='Analysis #')

        title_grp = HGroup(Item('auto_generate_title',
                                tooltip='Auto generate a title based on the analysis list'),
                           Item('title', springy=False,
                                enabled_when='not auto_generate_title',
                                tooltip='User specified plot title'),
                           icon_button_editor('edit_title_format_button', 'cog',
                                              enabled_when='auto_generate_title'),
                           label='Title', show_border=True)

        label_grp = VGroup(
            HGroup(Item('label_box'),
                   Item('analysis_label_display',
                        label='Label Format',
                        width=100,
                        style='readonly'),
                   spring,
                   icon_button_editor('edit_label_format_button', 'cog',
                                      tooltip='Open Label maker')),
            Item('label_all_peaks', label='Label Peaks', tooltip='Label each peak with its calculated age'),
            show_border=True, label='Label')
        inset_grp = VGroup(HGroup(Item('display_inset', label='Use'),
                                  Item('inset_location', label='Location'),
                                  Item('inset_width', label='Width'),
                                  Item('inset_height', label='Height')),
                           show_border=True,
                           label='Inset')
        mean_grp = VGroup(HGroup(Item('display_mean_indicator', label='Indicator'),
                                 Item('display_mean', label='Value',
                                      enabled_when='display_mean_indicator'),
                                 Item('display_percent_error', label='%Error',
                                      enabled_when='display_mean_indicator'),
                                 Item('mean_sig_figs', label='SigFigs')),
                          show_border=True,
                          label='Mean')
        info_grp = HGroup(Item('show_info', label='Show'),
                          Item('show_mean_info', label='Mean', enabled_when='show_info'),
                          Item('show_error_type_info', label='Error Type', enabled_when='show_info'),
                          show_border=True,
                          label='Info')

        display_grp = VGroup(mean_grp,
                             an_grp,
                             inset_grp,
                             title_grp,
                             label_grp,
                             info_grp,
                             errbar_grp,
                             scrollable=True,
                             show_border=True,
                             label='Display')

        return self._make_view(display_grp)


class CalculationSubOptions(SubOptions):
    def traits_view(self):
        calcgrp = Group(
            Item('probability_curve_kind',
                 width=-150,
                 label='Probability Curve Method'),
            Item('mean_calculation_kind',
                 width=-150,
                 label='Mean Calculation Method'),
            Item('error_calc_method',
                 width=-150,
                 label='Error Calculation Method'),
            Item('nsigma', label='Age Error NSigma'),
            HGroup(
                Item('include_j_error',
                     label='Include in Analyses'),
                Item('include_j_error_in_mean',
                     label='Include in Mean',
                     enabled_when='not include_j_error'),
                show_border=True, label='J Error'),

            Item('include_irradiation_error'),
            Item('include_decay_error'),
            show_border=True,
            label='Calculations')

        return self._make_view(calcgrp)


class IdeogramSubOptions(SubOptions):
    def traits_view(self):
        xgrp = VGroup(Item('index_attr',
                           editor=EnumEditor(name='index_attrs'),
                           label='X Value'),
                      HGroup(UItem('use_static_limits'),
                             Item('xlow', label='Min.',
                                  enabled_when='object.use_static_limits'),
                             Item('xhigh', label='Max.',
                                  enabled_when='object.use_static_limits'),
                             show_border=True,
                             label='Static Limits'),
                      HGroup(UItem('use_asymptotic_limits'),
                             # Item('asymptotic_width', label='% Width',
                             #      tooltip='Width of asymptotic section that is less than the Asymptotic %'),
                             Item('asymptotic_height_percent',
                                  tooltip='Percent of Max probability',
                                  label='% Height'),
                             # icon_button_editor('refresh_asymptotic_button', 'refresh',
                             #                    enabled_when='object.use_asymptotic_limits',
                             #                    tooltip='Refresh plot with defined asymptotic limits'),
                             enabled_when='not object.use_centered_range and not object.use_static_limits',
                             show_border=True,
                             label='Asymptotic Limits'),
                      HGroup(UItem('use_centered_range'),
                             UItem('centered_range',
                                   enabled_when='object.use_centered_range'),
                             label='Center on fixed range',
                             show_border=True,
                             enabled_when='not object.use_static_limits'),
                      HGroup(UItem('use_xpad'),
                             Item('xpad', label='Pad', enabled_when='use_xpad'),
                             Item('xpad_as_percent',
                                  tooltip='Treat Pad as a percent of the nominal width, otherwise Pad is in Ma. '
                                          'e.g if width=10 Ma, Pad=0.5 '
                                          'the final width will be 10 + (10*0.5)*2 = 20 Ma.',
                                  enabled_when='use_xpad',
                                  label='%'),
                             label='X Pad',
                             show_border=True),
                      show_border=True,
                      label='X')

        return self._make_view(xgrp)


class IdeogramAppearance(AppearanceSubOptions):
    def traits_view(self):
        mi = HGroup(Item('mean_indicator_fontname', label='Mean Indicator'),
                    Item('mean_indicator_fontsize', show_label=False))
        ee = HGroup(Item('error_info_fontname', label='Error Info'),
                    Item('error_info_fontsize', show_label=False))

        ll = HGroup(Item('label_fontname', label='Labels'),
                    Item('label_fontsize', show_label=False))
        fgrp = VGroup(UItem('fontname'),
                      mi, ee, ll,
                      HGroup(self._get_xfont_group(),
                             self._get_yfont_group()),
                      label='Fonts', show_border=True)

        g = VGroup(self._get_bg_group(),
                   self._get_padding_group(),
                   self._get_grid_group())
        return self._make_view(VGroup(g, fgrp))


class IdeogramMainOptions(MainOptions):
    def _get_edit_view(self):
        tooltip = """'Omit analyses based on the provided criteria. For example x>10 will omit any analysis
greater than 10. The value of x depends on the Auxiliary plot e.g. x is age for Analysis Number or K/Ca for KCa.
x is simply a placeholder and can be replaced by any letter or word except for a few exceptions
(i.e and, or, is, on, if, not...). To filter based on error or %error use "error" and "percent_error". Multiple predicates may be combined
with "and", "or". Valid comparators are "<,<=,>,>=,==,!=". "==" means "equals" and "!=" means is not equal.
Additional examples
1. x<10
2. age<10 or age>100
3. age<10 or error>1
4. x<=10 or percent_error>50
5. xyz<=10 and error>=0.1"""
        sigma_tooltip = """Omit analyses greater the N sigma from the arithmetic mean"""

        fgrp = VGroup(HGroup(Item('filter_str', tooltip=tooltip, label='Filter'),
                             UItem('filter_str_tag')),
                      HGroup(Item('sigma_filter_n', label='Sigma Filter N', tooltip=sigma_tooltip),
                             UItem('sigma_filter_tag')),
                      show_border=True,
                      label='Filtering')

        v = View(VGroup(HGroup(Item('name', editor=EnumEditor(name='names')),
                               Item('scale', editor=EnumEditor(values=['linear', 'log']))),
                        Item('height'),
                        HGroup(UItem('marker', editor=EnumEditor(values=marker_names)),
                               Item('marker_size', label='Size'),
                               show_border=True, label='Marker'),
                        HGroup(Item('ymin', label='Min'),
                               Item('ymax', label='Max'),
                               show_border=True,
                               label='Y Limits'),
                        fgrp,
                        show_border=True))
        return v


# ===============================================================
# ===============================================================
VIEWS = {}
VIEWS['main'] = IdeogramMainOptions
VIEWS['ideogram'] = IdeogramSubOptions
VIEWS['appearance'] = IdeogramAppearance
VIEWS['calculations'] = CalculationSubOptions
VIEWS['display'] = DisplaySubOptions
VIEWS['groups'] = GroupSubOptions


# ===============================================================
# ===============================================================


# ============= EOF =============================================
