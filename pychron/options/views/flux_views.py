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
from __future__ import absolute_import

from chaco.default_colormaps import color_map_name_dict
from traitsui.api import Item, HGroup, VGroup, Readonly, EnumEditor

from pychron.options.options import SubOptions, AppearanceSubOptions


class FluxSubOptions(SubOptions):
    def traits_view(self):
        calc_grp = VGroup(Item('selected_decay', label='Decay Const.'),
                          Readonly('lambda_k', label=u'Total \u03BB K'),
                          Readonly('monitor_age'),

                          Item('model_kind'),
                          Item('error_kind', label='Mean J Error'),
                          Item('predicted_j_error_type', label='Predicted J Error'),
                          Item('use_weighted_fit'),

                          Item('position_error', label='Position Error (Beta)',
                               tooltip='Set this value to the radius (same units as hole XY positions) of the '
                                       'irradiation hole. '
                                       'This is to test "monte carloing" the irradiation geometry'),
                          # Item('position_only', label='Position Only (Beta)',
                          #      enabled_when='position_error',
                          #      tooltip='Monte carlo only the position error, not J error. '
                          #              'used to see affect of position error'
                          #      ),

                          HGroup(Item('use_monte_carlo', label='Use'),
                                 Item('monte_carlo_ntrials', label='N. Trials',
                                      tooltip='Number of trials to perform monte carlo simulation'),
                                 show_border=True,
                                 label='Monte Carlo'),
                          show_border=True,
                          label='Calculations')

        grp = VGroup(Item('plot_kind'),
                     calc_grp)

        return self._make_view(grp)


class FluxAppearanceSubOptions(AppearanceSubOptions):
    def traits_view(self):
        twodgrp = VGroup(HGroup(Item('color_map_name',
                                     label='Color Map',
                                     editor=EnumEditor(values=sorted(color_map_name_dict.keys()))),
                                Item('levels')),
                         visible_when='plot_kind=="2D"',
                         label='Options',
                         show_border=True)
        onedgrp = VGroup(Item('marker_size'),
                         visible_when='plot_kind=="1D"',
                         label='Options',
                         show_border=True)
        return self._make_view(VGroup(twodgrp, onedgrp))


VIEWS = {'main': FluxSubOptions,
         'appearance': FluxAppearanceSubOptions}
# ============= EOF =============================================
