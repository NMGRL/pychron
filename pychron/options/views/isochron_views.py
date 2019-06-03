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
from pychron.options.options import SubOptions, AppearanceSubOptions, GroupSubOptions


class IsochronMainOptions(SubOptions):
    def traits_view(self):
        v = View()
        return v


class IsochronAppearance(AppearanceSubOptions):
    pass


class InverseIsochronMainOptions(SubOptions):
    def traits_view(self):
        g = Group(Item('error_calc_method',
                       width=-150,
                       label='Error Calculation Method'),
                  Item('regressor_kind', label='Method'),
                  show_border=True,
                  label='Calculations')

        info_grp = HGroup(Item('show_info', label='Info'),
                          BorderHGroup(UItem('info_fontname'),
                                       UItem('info_fontsize')))

        results_grp = HGroup(Item('show_results_info', label='Results'),
                             VGroup(BorderVGroup(HGroup(Item('nsigma', label='NSigma'),
                                                        Item('results_info_spacing',
                                                             editor=RangeEditor(mode='spinner', low=2,
                                                                                high=20, is_float=False),
                                                             label='Spacing')),
                                                 HGroup(UItem('results_fontname'),
                                                        UItem('results_fontsize'))),
                                    BorderHGroup(Item('age_sig_figs', label='Age'),
                                                 Item('yintercept_sig_figs', label='Y-Int.'),
                                                 label='SigFigs'),
                                    BorderVGroup(Item('include_4036_mse', label='Ar40/Ar36'),
                                                 Item('include_age_mse', label='Age'),
                                                 Item('include_percent_error', label='%Error'),
                                                 label='Include')))

        ellipse_grp = BorderHGroup(Item('fill_ellipses', label='fill'),
                                   Item('ellipse_kind', label='Kind'),
                                   label='Error Ellipse')
        label_grp = BorderVGroup(Item('show_labels'),
                                 HGroup(Item('label_box'),
                                        UItem('label_fontname'),
                                        UItem('label_fontsize'),
                                        enabled_when='show_labels'),
                                 label='Labels')

        marker_grp = BorderHGroup(Item('marker_size', label='Size'),
                                  Item('marker', label='Marker'),
                                  label='Marker')
        g2 = Group(BorderVGroup(info_grp,
                                results_grp,
                                label='Info'),
                   Item('include_error_envelope'),
                   marker_grp,
                   ellipse_grp,
                   label_grp,

                   BorderVGroup(Item('show_nominal_intercept'),
                                HGroup(Item('nominal_intercept_label', label='Label',
                                            enabled_when='show_nominal_intercept'),
                                       Item('nominal_intercept_value', label='Value',
                                            enabled_when='show_nominal_intercept')),
                                label='Nominal Intercept'),
                   BorderVGroup(Item('display_inset'),
                                Item('inset_location'),
                                HGroup(Item('inset_marker_size', label='Marker Size')),
                                HGroup(Item('inset_width', label='Width'),
                                       Item('inset_height', label='Height')),
                                label='Inset'),
                   show_border=True,
                   label='Display')
        return self._make_view(VGroup(g, g2))


class InverseIsochronAppearance(AppearanceSubOptions):
    pass


# ===============================================================
# ===============================================================

ISOCHRON_VIEWS = {'main': IsochronMainOptions,
                  'appearance': IsochronAppearance}
INVERSE_ISOCHRON_VIEWS = {'main': InverseIsochronMainOptions,
                          'appearance': InverseIsochronAppearance,
                          'groups': GroupSubOptions}

# ============= EOF =============================================
