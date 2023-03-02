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
from traits.api import Float, Bool, Int, Range, Enum, cached_property, Str

from pychron.core.fits.fit import IsoFilterFit
from pychron.options.aux_plot import AuxPlot
from pychron.options.fit import FitOptions
from pychron.options.views.iso_evo_views import VIEWS
from pychron.pychron_constants import FIT_TYPES, MAIN, AUTO_N


class IsoFilterFitAuxPlot(AuxPlot, IsoFilterFit):
    height = 0
    ofit = None
    goodness_threshold = Float  # in percent
    slope_goodness = Float
    slope_goodness_intensity = Float
    outlier_goodness = Int
    curvature_goodness = Float
    curvature_goodness_at = Float
    rsquared_goodness = Range(0.0, 1.0, 0.95)
    signal_to_blank_goodness = Float
    signal_to_baseline_goodness = Float
    signal_to_baseline_percent_goodness = Float
    fitfunc = Str
    filter_coefficients = Str("0.0003,0.5,0.00005,0.015")

    n_threshold = Int
    n_true = Enum(FIT_TYPES)
    n_false = Enum(FIT_TYPES)

    def smart_filter_values(self, xx):
        a, b, c, d = self.get_filter_coefficients()
        return a * xx**b + c * xx + d

    def get_filter_coefficients(self):
        return (float(f) for f in self.filter_coefficients.split(","))

    @cached_property
    def _get_fit_types(self):
        fts = super(IsoFilterFitAuxPlot, self)._get_fit_types()
        return fts + [AUTO_N]

    def auto_fit(self, n):
        if n >= self.n_threshold:
            fit = self.n_true
        else:
            fit = self.n_false

        return fit


class IsotopeEvolutionOptions(FitOptions):
    aux_plot_klass = IsoFilterFitAuxPlot

    show_sniff = Bool(False)

    def initialize(self):
        self.subview_names = [MAIN]
        for ap in self.aux_plots:
            if ap.fit == "Auto":
                ap.fit = AUTO_N

    def _get_subview(self, name):
        return VIEWS[name]


# ============= EOF =============================================
