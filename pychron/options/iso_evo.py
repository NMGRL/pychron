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
from traits.api import List, Float, Bool, Int, on_trait_change, Range, Enum, cached_property

from pychron.options.aux_plot import AuxPlot
from pychron.options.fit import FitOptions
from pychron.options.views.iso_evo_views import VIEWS
from pychron.core.fits.fit import IsoFilterFit
from pychron.pychron_constants import FIT_TYPES


class IsoFilterFitAuxPlot(AuxPlot, IsoFilterFit):
    names = List
    height = 0
    ofit = None
    goodness_threshold = Float  # in percent
    slope_goodness = Float
    slope_goodness_intensity = Float
    outlier_goodness = Int
    curvature_goodness = Float
    curvature_goodness_at = Float
    rsquared_goodness = Range(0.0, 1.0, 0.95)

    n_threshold = Int
    n_true = Enum(FIT_TYPES)
    n_false = Enum(FIT_TYPES)

    @cached_property
    def _get_fit_types(self):
        fts = super(IsoFilterFitAuxPlot, self)._get_fit_types()
        return fts + ['Auto', ]

    def auto_fit(self, n):
        if n >= self.n_threshold:
            fit = self.n_true
        else:
            fit = self.n_false

        return fit


class IsotopeEvolutionOptions(FitOptions):
    aux_plot_klass = IsoFilterFitAuxPlot
    subview_names = List(['Main', 'IsoEvo'])

    # global_goodness_threshold = Float  # in percent
    # global_slope_goodness = Float
    # global_outlier_goodness = Int
    # global_curvature_goodness = Float
    # global_curvature_goodness_at = Float
    #
    # # _main_options_klass = IsoEvoMainOptions
    show_sniff = Bool(False)

    #
    # @on_trait_change('global_+')
    # def _handle_goodness_global(self, name, new):
    #     items = self.selected
    #     if not items:
    #         items = self.aux_plots
    #
    #     name = name[7:]
    #     for a in items:
    #         setattr(a, name, new)

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
