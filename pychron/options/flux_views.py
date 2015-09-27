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
from chaco.default_colormaps import color_map_name_dict
from traitsui.api import View, Item, HGroup, VGroup, Readonly, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import SubOptions, AppearanceSubOptions


class FluxSubOptions(SubOptions):
    def traits_view(self):
        twodgrp = VGroup(HGroup(Item('color_map_name',
                                     label='Color Map',
                                     editor=EnumEditor(values=sorted(color_map_name_dict.keys()))),
                                Item('levels')),
                         Item('model_kind'),
                         visible_when='plot_kind=="2D"')
        onedgrp = VGroup(Item('marker_size'),
                         visible_when='plot_kind=="1D"')

        # ogrp = HGroup(Item('confirm_save',
        #                    label='Confirm Save', tooltip='Allow user to review evolutions '
        #                                                  'before saving to file'))
        grp = VGroup(Item('plot_kind'),
                     twodgrp,
                     onedgrp,
                     Item('selected_decay', label='Decay Const.'),
                     Readonly('lambda_k', label=u'Total \u03BB K'),
                     Item('monitor_age'),
                     Item('predicted_j_error_type', ),
                     Item('use_weighted_fit', ),
                     Item('monte_carlo_ntrials', ),
                     Item('use_monte_carlo', ),
                     label='Fits',
                     show_border=True)

        v = View(grp)
        return v


class FluxAppearanceSubOptions(AppearanceSubOptions):
    pass


VIEWS = {'main': FluxSubOptions,
         'appearance': FluxAppearanceSubOptions}
# ============= EOF =============================================
