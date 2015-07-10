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
from traits.api import Bool, Str, Int, Enum, Float, Property
from traitsui.api import View, Item, VGroup, HGroup, Tabbed, Readonly
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import EnumEditor
# from pychron.processing.fits.fit import IsoFilterFit
from pychron.pipeline.plot.options.base import dumpable
from pychron.pipeline.plot.options.figure_plotter_options import SaveableFigurePlotterOptions
# from pychron.processing.plot.options.option import AuxPlotOptions
from pychron.pychron_constants import ERROR_TYPES, K_DECAY_CONSTANTS


# class IsoFilterFitAuxPlot(AuxPlotOptions, IsoFilterFit):
#     names = List(['Ar40', 'Ar39'])
#     height = 0


class FluxOptions(SaveableFigurePlotterOptions):
    # plot_option_klass = IsoFilterFitAuxPlot
    color_map_name = dumpable(Str('jet'))
    marker_size = dumpable(Int(5))
    levels = dumpable(Int(50, auto_set=False, enter_set=True))

    error_kind = dumpable(Str('SD'))

    selected_decay = dumpable(Enum(K_DECAY_CONSTANTS.keys()))
    monitor_age = dumpable(Float(28.201))
    lambda_k = Property(depends_on='selected_decay')

    model_kind = dumpable(Enum('Plane', 'Bowl'))
    predicted_j_error_type = dumpable(Enum(*ERROR_TYPES))
    use_weighted_fit = dumpable(Bool(False))
    monte_carlo_ntrials = dumpable(Int(10))
    use_monte_carlo = dumpable(Bool(False))
    monitor_sample_name = dumpable(Str)
    plot_kind = dumpable((Enum('1D', '2D')))
    # def get_saveable_plots(self):
    #     return [p for p in self.aux_plots if p.use]

    def traits_view(self):
        bg_grp = self._get_bg_group()
        pd_grp = self._get_padding_group()
        a_grp = self._get_axes_group()
        appear_grp = VGroup(bg_grp, pd_grp, a_grp, label='Appearance')

        p_grp = self._get_fitting_group()

        v = View(Tabbed(p_grp, appear_grp))
        return v

    def _get_lambda_k(self):
        dc = K_DECAY_CONSTANTS[self.selected_decay]
        return dc[0] + dc[2]

    def _get_fitting_group(self):
        twodgrp = VGroup(HGroup(Item('color_map_name',
                                     label='Color Map',
                                     editor=EnumEditor(values=sorted(color_map_name_dict.keys()))),
                                Item('levels')),
                         Item('model_kind'),
                         visible_when='plot_kind=="2D"')
        onedgrp = VGroup(Item('marker_size'),
                         visible_when='plot_kind=="1D"')

        ogrp = HGroup(Item('confirm_save',
                           label='Confirm Save', tooltip='Allow user to review evolutions '
                                                         'before saving to file'))
        grp = VGroup(Item('plot_kind'),
                     twodgrp,
                     onedgrp,
                     Item('selected_decay', label='Total K Decay'),
                     Readonly('lambda_k'),
                     Item('monitor_age'),
                     Item('predicted_j_error_type', ),
                     Item('use_weighted_fit', ),
                     Item('monte_carlo_ntrials', ),
                     Item('use_monte_carlo', ))

        return VGroup(ogrp,
                      grp,
                      label='Fits')

# ============= EOF =============================================
