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
from traits.api import Str, Int, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.aux_plot import AuxPlot
from pychron.options.options import AuxPlotFigureOptions
from pychron.processing.fits.fit import Fit
from pychron.pychron_constants import FIT_ERROR_TYPES


class FitAuxPlot(AuxPlot, Fit):
    pass


class FitOptions(AuxPlotFigureOptions):
    global_fit = Str('Fit')
    global_error_type = Str('Error')
    nsigma = Int(1)
    use_time_axis = Bool(True)

    def set_names(self, names):
        for ai in self.aux_plots:
            if ai.name not in names:
                ai.plot_enabled = False
                ai.save_enabled = False
                ai.name = ''
            ai.names = names

    def set_detectors(self, dets):
        for p in self.aux_plots:
            p.detectors = dets

    # def traits_view(self):
    #     bg_grp = self._get_bg_group()
    #     pd_grp = self._get_padding_group()
    #     a_grp = self._get_axes_group()
    #     appear_grp = VGroup(bg_grp, pd_grp, a_grp, label='Appearance')
    #
    #     p_grp = self._get_aux_plots_group()
    #
    #     hgrp = self._misc_grp()
    #     v = View(VGroup(hgrp, Tabbed(p_grp, appear_grp)))
    #     return v
    #
    # def _get_columns(self):
    #     return [object_column(name='name'),
    #             checkbox_column(name='plot_enabled', label='Enabled'),
    #             checkbox_column(name='save_enabled', label='Save'),
    #             object_column(name='fit',
    #                           editor=EnumEditor(name='fit_types'),
    #                           width=75),
    #             object_column(name='error_type',
    #                           editor=EnumEditor(name='error_types'),
    #                           width=75, label='Error'),
    #             # checkbox_column(name='filter_outliers', label='Out.'),
    #             # object_column(name='filter_outlier_iterations', label='Iter.'),
    #             # object_column(name='filter_outlier_std_devs', label='SD'),
    #             # object_column(name='truncate', label='Trunc.'),
    #             # checkbox_column(name='include_baseline_error', label='Inc. BsErr')
    #             ]
    #
    # def _get_name_fit_group(self):
    #     h = HGroup(Item('name', editor=EnumEditor(name='names')),
    #                Item('fit', editor=EnumEditor(name='fit_types')),
    #                UItem('error_type', editor=EnumEditor(name='error_types'))),
    #     return h
    #
    # def _get_edit_view(self):
    #     return View(VGroup(self._get_name_fit_group(),
    #                        Item('marker', editor=EnumEditor(values=marker_names)),
    #                        Item('marker_size'),
    #                        HGroup(Item('ymin', label='Min'),
    #                               Item('ymax', label='Max'),
    #                               show_border=True,
    #                               label='Y Limits'),
    #                        show_border=True))

    # def _get_aux_plots_item(self):
    #     aux_plots_item = UItem('aux_plots',
    #                            style='custom',
    #                            show_label=False,
    #                            editor=myTableEditor(columns=self._get_columns(),
    #                                                 sortable=False,
    #                                                 deletable=False,
    #                                                 clear_selection_on_dclicked=True,
    #                                                 edit_on_first_click=False,
    #                                                 selection_mode='rows',
    #                                                 selected='selected_aux_plots',
    #                                                 # on_select=lambda *args: setattr(self, 'selected', True),
    #                                                 # selected='selected',
    #                                                 edit_view=self._get_edit_view(),
    #                                                 reorderable=False))
    #     return aux_plots_item
    #
    # def _get_aux_plots_group(self):
    #     ggrp = VGroup(HGroup(UItem('global_fit', editor=EnumEditor(name='fit_types')),
    #                          UItem('global_error_type', editor=EnumEditor(name='error_types'))))
    #     api = self._get_aux_plots_item()
    #     return Group(VGroup(ggrp, api), label='Fits')
    #
    # def _misc_grp(self):
    #     ogrp = HGroup(Item('use_plotting',
    #                        label='Use Plotting',
    #                        tooltip='(Checked) Plot the isotope evolutions '
    #                                '(Non-checked) Only calculate new fit results. Do not plot'))
    #     return ogrp

    # def _get_aux_plots_group(self):
    #     return Group(self._get_aux_plots_item(), label='Fits')

    def _get_aux_plots(self):
        fs = self.selected_aux_plots
        if not fs:
            fs = self.aux_plots
        return fs

    def _global_fit_changed(self):
        # if self.global_fit in self.fit_types:
        fs = self._get_aux_plots()
        for fi in fs:
            fi.fit = self.global_fit

    def _global_error_type_changed(self):
        if self.global_error_type in FIT_ERROR_TYPES:
            fs = self._get_aux_plots()
            for fi in fs:
                fi.error_type = self.global_error_type

# ============= EOF =============================================
