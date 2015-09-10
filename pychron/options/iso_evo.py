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
from traits.api import List
from traitsui.api import EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.aux_plot import AuxPlot
from pychron.options.fit import FitOptions
from pychron.options.iso_evo_views import VIEWS
from pychron.options.options import checkbox_column, object_column, MainOptions
from pychron.processing.fits.fit import IsoFilterFit


class IsoFilterFitAuxPlot(AuxPlot, IsoFilterFit):
    names = List
    height = 0
    ofit = None


class IsoEvoMainOptions(MainOptions):
    def _get_columns(self):
        cols = [object_column(name='name', editable=False),
                checkbox_column(name='plot_enabled', label='Plot'),
                checkbox_column(name='save_enabled', label='Save'),
                object_column(name='fit',
                              editor=EnumEditor(name='fit_types'),
                              width=75),
                object_column(name='error_type',
                              editor=EnumEditor(name='error_types'),
                              width=75, label='Error'),
                checkbox_column(name='filter_outliers', label='Out.'),
                object_column(name='filter_outlier_iterations', label='Iter.'),
                object_column(name='filter_outlier_std_devs', label='SD'),
                object_column(name='truncate', label='Trunc.'),
                checkbox_column(name='include_baseline_error', label='Inc. BsErr')]
        return cols


class IsotopeEvolutionOptions(FitOptions):
    aux_plot_klass = IsoFilterFitAuxPlot
    subview_names = List(['Main', 'IsoEvo', 'Appearance'])
    _main_options_klass = IsoEvoMainOptions

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
