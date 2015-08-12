# ===============================================================================
# Copyright 2013 Jake Ross
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
from traitsui.api import View, VGroup, Tabbed, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.processing.plot.options.option import GroupablePlotterOptions
# from pychron.processing.plotters.options.base import FigurePlotterOptions
# from pychron.processing.plot.options import FitPlotterOptions
# from pychron.pipeline.plot.options import GroupablePlotterOptions
# from pychron.pipeline.plot.options.option import FitPlotterOptions
from pychron.pipeline.plot.options.figure_plotter_options import object_column, checkbox_column
from pychron.pipeline.plot.options.fit import FitAuxPlot, FitOptions


# class SeriesOptions(GroupablePlotterOptions):
from pychron.pychron_constants import ARGON_KEYS, FIT_TYPES


class SeriesFitAuxPlot(FitAuxPlot):
    def _get_fit_types(self):
        return FIT_TYPES


class SeriesOptions(FitOptions):
    aux_plot_klass = SeriesFitAuxPlot
    # groups = List
    # aux_plot_klass = FitAuxPlot

    def _aux_plots_default(self):
        def f(kii):
            ff = FitAuxPlot(name=kii)
            ff.trait_set(plot_enabled=False,
                         save_enabled=False, fit='')

            return ff

        keys = list(ARGON_KEYS)
        keys.extend(['{}bs'.format(ki) for ki in ARGON_KEYS])
        keys.extend(['{}ic'.format(ki) for ki in ARGON_KEYS])
        if 'Ar40' in keys:
            if 'Ar39' in keys:
                keys.append('Ar40/Ar39')
                keys.append('uAr40/Ar39')
            if 'Ar36' in keys:
                keys.append('Ar40/Ar36')
                keys.append('uAr40/Ar36')

        keys.append('Peak Center')
        keys.append('AnalysisType')

        return [f(k) for k in keys]

    def _get_columns(self):
        return [object_column(name='name', width=125),
                checkbox_column(name='plot_enabled', label='Plot'),
                object_column(name='fit',
                              editor=EnumEditor(name='fit_types'),
                              width=75),
                object_column(name='error_type',
                              editor=EnumEditor(name='error_types'),
                              width=75, label='Error'),
                checkbox_column(name='y_error', label='YError')]

    def traits_view(self):
        bg_grp = self._get_bg_group()
        pd_grp = self._get_padding_group()
        a_grp = self._get_axes_group()
        appear_grp = VGroup(bg_grp, pd_grp, a_grp, label='Appearance')

        p_grp = self._get_aux_plots_group()

        v = View(VGroup(Tabbed(p_grp, appear_grp)))
        return v

# ============= EOF =============================================
    # def load_aux_plots(self, ref):
    #     def f(kii):
    #         ff = next((x for x in self.aux_plots if x.name == kii), None)
    #         if not ff:
    #             ff = FitAuxPlot(name=kii)
    #             ff.trait_set(use=False, fit='')
    #
    #         return ff
    #
    #     keys = ref.isotope_keys
    #     ks = ref.isotope_keys[:]
    #     keys.extend(['{}bs'.format(ki) for ki in ks])
    #     keys.extend(['{}ic'.format(ki) for ki in ks])
    #     if 'Ar40' in keys:
    #         if 'Ar39' in keys:
    #             keys.append('Ar40/Ar39')
    #             keys.append('uAr40/Ar39')
    #         if 'Ar36' in keys:
    #             keys.append('Ar40/Ar36')
    #             keys.append('uAr40/Ar36')
    #
    #     keys.append('PC')
    #     keys.append('AnalysisType')
    #
    #     ap = [f(k) for k in keys]
    #     self.trait_set(aux_plots=ap)
