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
from traitsui.api import View, Item, HGroup, VGroup, Group, UItem, RangeEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options import SubOptions, AppearanceSubOptions, GroupSubOptions, TitleSubOptions
from pychron.pychron_constants import FLECK_PLATEAU_DEFINITION, MAHON_PLATEAU_DEFINITION, GROUPS, APPEARANCE, MAIN, \
    INSET, CALCULATIONS


class IsochronMainOptions(SubOptions):
    def traits_view(self):
        v = View()
        return v


class IsochronAppearance(AppearanceSubOptions):
    pass


class InverseIsochronCalculationOptions(SubOptions):
    def traits_view(self):
        plat_grp = BorderHGroup(VGroup(Item('omit_non_plateau', label='Omit Non Plateau Steps',
                                            tooltip='Displays the non plateau steps but they are not used in the '
                                                    'calculations'),
                                       Item('exclude_non_plateau',
                                            label='Exclude Non Plateau Steps',
                                            tooltip='Only plot plateau steps')),
                                HGroup(Item('plateau_method',
                                            tooltip='Fleck 1977={}\n'
                                                    'Mahon 1996={}'.format(FLECK_PLATEAU_DEFINITION,
                                                                           MAHON_PLATEAU_DEFINITION),
                                            label='Method'),
                                       icon_button_editor('edit_plateau_criteria', 'cog',
                                                          tooltip='Edit Plateau Criteria'),
                                       visible_when='omit_non_plateau'),
                                label='Plateau')

        g = BorderHGroup(Item('regressor_kind', label='Method'),
                         Item('error_calc_method',
                              width=-150,
                              label='Error Calculation Method'),
                         label='Regression')

        return self._make_view(VGroup(g, plat_grp))


class InverseIsochronMainOptions(TitleSubOptions):
    def traits_view(self):
        info_grp = BorderHGroup(Item('show_info', label='Display Info',
                                     tooltip='Display info text in the upper left corner. Displays info on '
                                             'uncertainties'),
                                BorderHGroup(UItem('info_fontname'),
                                             UItem('info_fontsize'),
                                             enabled_when='show_info'),
                                label='Info')

        agrp = HGroup(BorderHGroup(Item('nsigma', label='NSigma'),
                                   Item('results_info_spacing',
                                        editor=RangeEditor(mode='spinner', low=2,
                                                           high=20, is_float=False),
                                        label='Spacing')),
                      BorderHGroup(UItem('results_fontname'),
                                   UItem('results_fontsize')))
        bgrp = HGroup(BorderHGroup(Item('include_4036_mse', label='MSE'),
                                   Item('include_percent_error', label='%Err.'),
                                   Item('yintercept_sig_figs', label='SigFigs'),
                                   label='Ar40/Ar36'),
                      BorderHGroup(Item('include_age_mse', label='MSE'),
                                   Item('include_age_percent_error', label='%Err.'),
                                   Item('age_sig_figs', label='SigFigs'),
                                   label='Age'), )

        tgrp = BorderVGroup(Item('omit_by_tag', label='Omit Tags',
                                 tooltip='If selected only analyses tagged as "OK" are included in the calculations'),
                            label='Tags')

        results_grp = BorderVGroup(Item('show_results_info', label='Display Results'),
                                   VGroup(agrp, bgrp, enabled_when='show_results_info'),
                                   label='Results')

        error_display_grp = BorderHGroup(Item('fill_ellipses', label='Fill'),
                                         Item('ellipse_kind', label='Kind'),
                                         Item('include_error_envelope'),
                                         label='Error Display')
        label_grp = BorderVGroup(Item('show_labels', label='Display Labels'),
                                 HGroup(Item('label_box'),
                                        UItem('label_fontname'),
                                        UItem('label_fontsize'),
                                        enabled_when='show_labels'),
                                 label='Labels')

        marker_grp = BorderHGroup(Item('marker_size', label='Size'),
                                  Item('marker', label='Marker'),
                                  label='Marker')
        g2 = Group(self._get_title_group(),
                   info_grp,
                   results_grp,
                   marker_grp,
                   error_display_grp,
                   label_grp,
                   tgrp,
                   BorderVGroup(Item('show_nominal_intercept'),
                                HGroup(Item('nominal_intercept_label', label='Label',
                                            enabled_when='show_nominal_intercept'),
                                       Item('nominal_intercept_value', label='Value',
                                            enabled_when='show_nominal_intercept')),
                                label='Nominal Intercept'))
        return self._make_view(g2)


class InverseIsochronInset(SubOptions):
    def traits_view(self):

        xbounds = BorderHGroup(Item('inset_xmin', label='Min.'),
                               Item('inset_xmax', label='Max.'),
                               label='X Limits')
        ybounds = BorderHGroup(Item('inset_ymin', label='Min.'),
                               Item('inset_ymax', label='Max.'),
                               label='Y Limits')
        e = BorderHGroup(Item('inset_show_error_ellipse', label='Show'),
                         Item('inset_fill_ellipses', label='Fill'),
                         Item('inset_ellipse_kind', label='Kind'),
                         label='Error Ellipse')

        g = VGroup(Item('display_inset'),
                   Item('inset_location'),
                   HGroup(Item('inset_marker_size', label='Marker Size')),
                   HGroup(Item('inset_show_axes_titles', label='Show Axes Titles')),
                   HGroup(Item('inset_width', label='Width'),
                          Item('inset_height', label='Height')),
                   HGroup(Item('inset_label_fontname', label='Label Font'),
                          UItem('inset_label_fontsize')),
                   HGroup(Item('inset_link_status', label='Link Omit Status',
                               tooltip='When enabled, link omit status between main and inset plots')),
                   xbounds,
                   ybounds,
                   e)

        return self._make_view(g)


class InverseIsochronAppearance(AppearanceSubOptions):
    pass


# ===============================================================
# ===============================================================

ISOCHRON_VIEWS = {MAIN.lower(): IsochronMainOptions,
                  APPEARANCE.lower(): IsochronAppearance}

INVERSE_ISOCHRON_VIEWS = {MAIN.lower(): InverseIsochronMainOptions,
                          CALCULATIONS.lower(): InverseIsochronCalculationOptions,
                          APPEARANCE.lower(): InverseIsochronAppearance,
                          INSET.lower(): InverseIsochronInset,
                          GROUPS.lower(): GroupSubOptions}

# ============= EOF =============================================
