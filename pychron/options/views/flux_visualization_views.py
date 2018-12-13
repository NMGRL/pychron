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
from traitsui.api import Item, HGroup, VGroup, EnumEditor

from pychron.options.options import SubOptions, AppearanceSubOptions


class FluxVisualizationSubOptions(SubOptions):
    def traits_view(self):
        grp = VGroup(Item('plot_kind'),
                     Item('model_kind'))
        return self._make_view(grp)


class FluxVisualizationAppearanceSubOptions(AppearanceSubOptions):
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
        scalegrp = VGroup(Item('flux_scalar', label='Scale', tooltip='Multiple flux by Scale. FOR DISPLAY ONLY'))
        return self._make_view(VGroup(twodgrp, onedgrp, scalegrp))


VIEWS = {'main': FluxVisualizationSubOptions,
         'appearance': FluxVisualizationAppearanceSubOptions}
# ============= EOF =============================================
