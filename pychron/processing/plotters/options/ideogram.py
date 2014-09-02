#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import Enum, Float, Bool, String
from traitsui.api import Item, HGroup, Group, VGroup, UItem, EnumEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.plotters.options.age import AgeOptions


class IdeogramOptions(AgeOptions):
    probability_curve_kind = Enum('cumulative', 'kernel')
    mean_calculation_kind = Enum('weighted mean', 'kernel')
    error_calc_method = Enum('SEM, but if MSWD>1 use SEM * sqrt(MSWD)', 'SEM')

    xlow = Float
    xhigh = Float
    use_centered_range = Bool
    centered_range = Float(0.5)

    display_mean_indicator = Bool(True)
    display_mean = Bool(True)
    plot_option_name = 'Ideogram'
    # index_attr = Enum('Age', 'Ar40*/Ar39k','Ar40/Ar36')
    index_attr=String
    use_asymptotic_limits = Bool
    asymptotic_width = Float
    x_end_caps = Bool(False)
    y_end_caps = Bool(False)

    # def _index_attr_default(self):
    #     return 'uage'
    def _index_attr_changed(self):
        for ap in self.aux_plots:
            ap.clear_ylimits()

    def _get_groups(self):
        xgrp = VGroup(HGroup(Item('index_attr',
                                  editor=EnumEditor(values={'uage':'01:Age',
                                                            'uF':'02:Ar40*/Ar39k',
                                                            'Ar40/Ar36': '03:Ar40/Ar36',
                                                            'Ar40/Ar39': '04:Ar40/Ar39',
                                                            'Ar40/Ar38': '05:Ar40/Ar38',
                                                            'Ar39/Ar37':'06:Ar39/Ar37',
                                                            'Ar40':'07:Ar40',
                                                            'Ar39':'08:Ar39',
                                                            'Ar38':'09:Ar38',
                                                            'Ar37':'10:Ar37',
                                                            'Ar36':'11:Ar36',}),
                                  label='X Value'),
                             Item('xlow', label='Min.', enabled_when='not object.use_centered_range'),
                             Item('xhigh', label='Max.', enabled_when='not object.use_centered_range')),
                      HGroup(Item('use_asymptotic_limits', enabled_when='not object.use_centered_range'),
                             Item('asymptotic_width', label='Width',
                                  enabled_when='object.use_asymptotic_limits')),
                      HGroup(Item('use_centered_range', label='Center on fixed range'),
                             UItem('centered_range',
                                   enabled_when='object.use_centered_range')),
                      label='Index')

        g = Group(
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
            Item('include_j_error'),
            Item('include_irradiation_error'),
            Item('include_decay_error'),
            label='Calculations')

        g2 = Group(HGroup(Item('display_mean_indicator', label='Indicator'),
                          Item('display_mean', label='Value'),
                          label='Mean'),
                   Item('label_box'),
                   HGroup(Item('show_info', label='Show'),
                          Item('show_mean_info', label='Mean', enabled_when='show_info'),
                          Item('show_error_type_info', label='Error Type', enabled_when='show_info'),
                          label='Info'),
                   label='Display')

        egrp = Group(HGroup(Item('x_end_caps', label='X'),
                            Item('y_end_caps', label='Y'),
                            label='End Caps', ),
                     label='Error Bars')
        return VGroup(self._get_title_group(),
                      xgrp,
                      g, g2, egrp,
                      label='Options'),


    def _get_dump_attrs(self):
        attrs = super(IdeogramOptions, self)._get_dump_attrs()
        return attrs + [
            'probability_curve_kind',
            'mean_calculation_kind',
            'error_calc_method',
            'xlow', 'xhigh',
            'use_centered_range', 'centered_range',
            'use_asymptotic_limits', 'asymptotic_width',
            'display_mean', 'display_mean_indicator',
            'x_end_caps','y_end_caps','index_attr'
        ]

#============= EOF =============================================
