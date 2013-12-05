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
from traits.api import Enum, Float, Bool
from traitsui.api import Item, HGroup, Group

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

    def _get_x_axis_group(self):
        vg = super(IdeogramOptions, self)._get_x_axis_group()

        limits_grp = HGroup(Item('xlow', label='Min.'),
                            Item('xhigh', label='Max.'),
                            enabled_when='not object.use_centered_range')
        centered_grp = HGroup(Item('use_centered_range', label='Center'),
                              Item('centered_range', show_label=False,
                                   enabled_when='object.use_centered_range'))
        vg.content.append(limits_grp)
        vg.content.append(centered_grp)

        return vg

    def _get_groups(self):
        g = Group(
            Item('show_info', label='Display Info.'),
            Item('_'),
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

            label='Calculations'
        )
        return (g,)

    def _get_dump_attrs(self):
        attrs = super(IdeogramOptions, self)._get_dump_attrs()
        return attrs + [
            'probability_curve_kind',
            'mean_calculation_kind',
            'error_calc_method',
            'xlow', 'xhigh',
            'use_centered_range', 'centered_range'
        ]

#============= EOF =============================================
