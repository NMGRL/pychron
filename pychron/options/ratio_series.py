# ===============================================================================
# Copyright 2019 ross
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
from traits.api import Property, List, Float, Str

from pychron.options.series import SeriesOptions, SeriesFitAuxPlot
from pychron.options.views.ratio_series_views import VIEWS
from pychron.pychron_constants import NULL_STR, FIT_TYPES_INTERPOLATE, MAIN, APPEARANCE


class RatioSeriesAuxPlot(SeriesFitAuxPlot):
    name = Property
    detectors = List
    numerator = Str
    denominator = Str

    standard_ratio = Float
    standard_ratios = List((295.5,))

    def _get_name(self):
        if self.denominator and self.denominator != NULL_STR:
            ret = '{}/{}'.format(self.numerator, self.denominator)
        else:
            ret = self.numerator
        return ret

    def _get_fit_types(self):
        return FIT_TYPES_INTERPOLATE


class RatioSeriesOptions(SeriesOptions):
    aux_plot_klass = RatioSeriesAuxPlot

    def initialize(self):
        self.subview_names = [MAIN, 'Ratio Series', APPEARANCE]

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
