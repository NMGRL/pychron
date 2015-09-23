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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options import SubOptions, AppearanceSubOptions, GroupSubOptions


class SpectrumSubOptions(SubOptions):
    traits_view = View()


class SpectrumAppearance(AppearanceSubOptions):
    def traits_view(self):
        ee = HGroup(Item('error_info_fontname', label='Error Info'),
                    UItem('error_info_fontsize'))

        ll = HGroup(Item('label_fontname', label='Labels'),
                    UItem('label_fontsize'))

        pp = HGroup(Item('plateau_fontname', label='Plateau'),
                    UItem('plateau_fontsize'))
        ii = HGroup(Item('integrated_fontname', label='Integrated'),
                    UItem('integrated_fontsize'))

        fgrp = VGroup(UItem('fontname'),
                      ee, ll, pp, ii,
                      HGroup(self._get_xfont_group(),
                             self._get_yfont_group()),
                      label='Fonts', show_border=True)

        v = View(VGroup(self._get_bg_group(),
                        self._get_padding_group(),

                        fgrp))
        return v


class DisplaySubOptions(SubOptions):
    def traits_view(self):
        display_grp = Group(HGroup(UItem('show_info',
                                         tooltip='Show general info in the upper right corner'),
                                   show_border=True,
                                   label='General'),
                            VGroup(Item('include_legend', label='Show'),
                                   Item('include_sample_in_legend', label='Include Sample'),
                                   Item('legend_location', label='Location'),
                                   label='Legend', show_border=True),

                            HGroup(Item('display_step', label='Step'),
                                   Item('display_extract_value', label='Power/Temp'),
                                   # spring,
                                   # Item('step_label_font_size', label='Size'),
                                   show_border=True,
                                   label='Labels'),
                            VGroup(HGroup(UItem('display_plateau_info',
                                                tooltip='Display plateau info'),
                                          # Item('plateau_font_size', label='Size',
                                          #      enabled_when='display_plateau_info'),
                                          Item('plateau_sig_figs', label='SigFigs')),
                                   HGroup(Item('include_plateau_sample',
                                               tooltip='Add the Sample name to the Plateau indicator',
                                               label='Sample'),
                                          Item('include_plateau_identifier',
                                               tooltip='Add the Identifier to the Plateau indicator',
                                               label='Identifier')),
                                   Item('plateau_arrow_visible'),
                                   show_border=True,
                                   label='Plateau'),
                            HGroup(UItem('display_integrated_info',
                                         tooltip='Display integrated age info'),
                                   # Item('integrated_font_size', label='Size',
                                   #      enabled_when='display_integrated_info'),
                                   Item('integrated_sig_figs', label='SigFigs'),
                                   show_border=True,
                                   label='Integrated'),
                            show_border=True,
                            label='Display')
        v = View(display_grp)
        return v


class CalculationSubOptions(SubOptions):
    def traits_view(self):
        lgrp = VGroup(Item('plateau_method', label='Method'),
                      Item('nsigma'),
                      Item('plateau_age_error_kind',
                           width=-100,
                           label='Error Type'),
                      Item('include_j_error_in_plateau', label='Include J Error'))
        rgrp = VGroup(Item('center_line_style',
                           label='Line Stype'),
                      Item('extend_plateau_end_caps',
                           label='Extend End Caps'),
                      icon_button_editor('edit_plateau_criteria', 'cog',
                                         tooltip='Edit Plateau Criteria'), )
        plat_grp = HGroup(lgrp, rgrp)

        # grp_grp = VGroup(UItem('group',
        #                        style='custom',
        #                        editor=InstanceEditor(view='simple_view')),
        #                  show_border=True,
        #                  label='Group Attributes')

        error_grp = VGroup(HGroup(Item('step_nsigma',
                                       editor=EnumEditor(values=[1, 2, 3]),
                                       tooltip='Set the size of the error envelope in standard deviations',
                                       label='N. Sigma')),
                           show_border=True,
                           label='Error Envelope')
        v = View(VGroup(plat_grp, error_grp))
        return v


VIEWS = {}
VIEWS['spectrum'] = SpectrumSubOptions
VIEWS['appearance'] = SpectrumAppearance
VIEWS['calculations'] = CalculationSubOptions
VIEWS['display'] = DisplaySubOptions
VIEWS['groups'] = GroupSubOptions
# ============= EOF =============================================
