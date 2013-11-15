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
from traits.api import HasTraits, Str, Bool, Property, Int, Enum

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pychron_constants import NULL_STR, FIT_TYPES


class PlotterOption(HasTraits):
    use = Bool
    name = Str(NULL_STR)
    plot_names = Property

    scale = Enum('linear', 'log')
    height = Int(100, enter_set=True, auto_set=False)
    x_error = Bool(False)
    y_error = Bool(False)
    show_labels = Bool(False)

    normalize = None
    use_time_axis = False

    def _name_changed(self):
        if self.name != NULL_STR:
            self.use = True

    def _get_plot_names(self):
        return {NULL_STR: NULL_STR,
                'analysis_number_stacked': 'Analysis Number Stacked',
                'analysis_number': 'Analysis Number',
                'radiogenic_yield': 'Radiogenic 40Ar',
                'kca': 'K/Ca',
                'kcl': 'K/Cl',
                'moles_K39': 'K39 Moles',
                'relative_probability': 'Ideogram'}


class FitPlotterOption(PlotterOption):
    fit = Enum(['', ] + FIT_TYPES)


class SpectrumPlotOption(PlotterOption):
    def _get_plot_names(self):
        return {NULL_STR: NULL_STR,
                'radiogenic_yield': 'Radiogenic 40Ar',
                'kca': 'K/Ca',
                'kcl': 'K/Cl',
                'moles_K39': 'K39 Moles',
                'age_spectrum': 'Age'}


class InverseIsochronPlotOption(PlotterOption):
    def _get_plot_names(self):
        return {NULL_STR: NULL_STR,
                #'radiogenic_yield': 'Radiogenic 40Ar',
                #'kca': 'K/Ca',
                #'kcl': 'K/Cl',
                #'moles_K39': 'K39 Moles',
                'inverse_isochron': 'Inv. Isochron'}


class SystemMonitorPlotOption(PlotterOption):
    _auto_set_use = False
    normalize = 'now'
    use_time_axis = True

    def _name_changed(self):
        pass

#============= EOF =============================================
