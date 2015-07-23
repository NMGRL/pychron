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
from enable.markers import marker_names
from traitsui.api import View, Item, HGroup, VGroup, EnumEditor, Tabbed, Group
from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.processing.analyses.analysis import Fit
from pychron.core.ui.table_editor import myTableEditor
from pychron.pipeline.plot.options.figure_plotter_options import SaveableFigurePlotterOptions, object_column, \
    checkbox_column
from pychron.processing.fits.fit import Fit
# from pychron.pipeline.plot.options import object_column, \
#     checkbox_column, SaveableFigurePlotterOptions
from pychron.pipeline.plot.options.option import AuxPlotOptions
from pychron.pychron_constants import FIT_TYPES_INTERPOLATE, ARGON_KEYS


class FitAuxPlot(AuxPlotOptions, Fit):
    names = List(ARGON_KEYS)

    def _get_fit_types(self):
        return FIT_TYPES_INTERPOLATE


class FitOptions(SaveableFigurePlotterOptions):
    aux_plot_klass = FitAuxPlot

    def set_detectors(self, dets):
        for p in self.aux_plots:
            p.detectors = dets

    # def get_saveable_plots(self):
    #     return [p for p in self.aux_plots if p.use]

    def traits_view(self):
        bg_grp = self._get_bg_group()
        pd_grp = self._get_padding_group()
        a_grp = self._get_axes_group()
        appear_grp = VGroup(bg_grp, pd_grp, a_grp, label='Appearance')

        p_grp = self._get_aux_plots_group()

        hgrp = self._button_grp()
        v = View(VGroup(hgrp, Tabbed(p_grp, appear_grp)))
        return v

    def _get_columns(self):
        return [object_column(name='name'),
                checkbox_column(name='plot_enabled', label='Enabled'),
                checkbox_column(name='save_enabled', label='Save'),
                object_column(name='fit',
                              editor=EnumEditor(name='fit_types'),
                              width=75),
                object_column(name='error_type',
                              editor=EnumEditor(name='error_types'),
                              width=75, label='Error'),
                # checkbox_column(name='filter_outliers', label='Out.'),
                # object_column(name='filter_outlier_iterations', label='Iter.'),
                # object_column(name='filter_outlier_std_devs', label='SD'),
                # object_column(name='truncate', label='Trunc.'),
                # checkbox_column(name='include_baseline_error', label='Inc. BsErr')
                ]

    def _get_edit_view(self):
        return View(VGroup(Item('name', editor=EnumEditor(name='names'), width=150),
                           Item('marker', editor=EnumEditor(values=marker_names)),
                           Item('marker_size'),
                           HGroup(Item('ymin', label='Min'),
                                  Item('ymax', label='Max'),
                                  show_border=True,
                                  label='Y Limits'),
                           show_border=True))

    def _get_aux_plots_group(self):
        aux_plots_grp = Item('aux_plots',
                             style='custom',
                             show_label=False,
                             editor=myTableEditor(columns=self._get_columns(),
                                                  sortable=False,
                                                  deletable=False,
                                                  clear_selection_on_dclicked=True,
                                                  edit_on_first_click=False,
                                                  # on_select=lambda *args: setattr(self, 'selected', True),
                                                  # selected='selected',
                                                  edit_view=self._get_edit_view(),
                                                  reorderable=False))
        return Group(aux_plots_grp, label='Fits')

# ============= EOF =============================================
