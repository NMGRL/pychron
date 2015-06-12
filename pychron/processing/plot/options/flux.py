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
from traits.api import List, Bool, Str, Int, Enum
from traitsui.api import View, Item, VGroup, HGroup, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.fits.fit import IsoFilterFit
from pychron.processing.plot.options.base import dumpable
from pychron.processing.plot.options.figure_plotter_options import FigurePlotterOptions
from pychron.processing.plot.options.option import AuxPlotOptions


class IsoFilterFitAuxPlot(AuxPlotOptions, IsoFilterFit):
    names = List(['Ar40', 'Ar39'])
    height = 0


class FluxOptions(FigurePlotterOptions):
    # plot_option_klass = IsoFilterFitAuxPlot
    use_plotting = dumpable(Bool(True))
    confirm_save = dumpable(Bool)

    error_kind = 'SD'
    monitor_age = 28.201
    lambda_k = 5.464e-10

    model_kind = dumpable(Str('Plane'))
    predicted_j_error_type = dumpable(Str('SD'))
    use_weighted_fit = dumpable(Bool(False))
    monte_carlo_ntrials = dumpable(Int(10))
    use_monte_carlo = dumpable(Bool(False))
    monitor_sample_name = dumpable(Str)
    plot_kind = dumpable((Enum('Contour', 'Sin')))
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

    def _get_fitting_group(self):
        # cols = [object_column(name='name', editable=False),
        #         checkbox_column(name='enabled', label='Plot'),
        #         checkbox_column(name='use', label='Save'),
        #         object_column(name='fit',
        #                       editor=EnumEditor(name='fit_types'),
        #                       width=75),
        #         object_column(name='error_type',
        #                       editor=EnumEditor(name='error_types'),
        #                       width=75, label='Error'),
        #         checkbox_column(name='filter_outliers', label='Out.'),
        #         object_column(name='filter_outlier_iterations', label='Iter.'),
        #         object_column(name='filter_outlier_std_devs', label='SD'),
        #         object_column(name='truncate', label='Trunc.'),
        #         checkbox_column(name='include_baseline_error', label='Inc. BsErr')]
        #
        # v = View(VGroup(Item('name', editor=EnumEditor(name='names')),
        #                 Item('marker', editor=EnumEditor(values=marker_names)),
        #                 Item('marker_size'),
        #                 HGroup(Item('ymin', label='Min'),
        #                        Item('ymax', label='Max'),
        #                        show_border=True,
        #                        label='Y Limits'),
        #                 show_border=True))

        # aux_plots_grp = Item('aux_plots',
        #                      style='custom',
        #                      show_label=False,
        #                      editor=myTableEditor(columns=cols,
        #                                           sortable=False,
        #                                           deletable=False,
        #                                           clear_selection_on_dclicked=True,
        #                                           edit_on_first_click=False,
        #                                           # on_select=lambda *args: setattr(self, 'selected', True),
        #                                           # selected='selected',
        #                                           edit_view=v,
        #                                           reorderable=False))
        ogrp = HGroup(Item('confirm_save',
                           label='Confirm Save', tooltip='Allow user to review evolutions '
                                                         'before saving to file'))
        grp = VGroup(Item('plot_kind'),
                     Item('model_kind', ),
                     Item('predicted_j_error_type', ),
                     Item('use_weighted_fit', ),
                     Item('monte_carlo_ntrials', ),
                     Item('use_monte_carlo', ))

        return VGroup(ogrp,
                      grp,
                      label='Fits')

# ============= EOF =============================================
