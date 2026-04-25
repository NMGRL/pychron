# ===============================================================================
# Copyright 2018 ross
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
from traits.api import Str, Float, Property, cached_property

from pychron.core.helpers.formatting import floatfmt
from pychron.pipeline.results.base import BaseResult

GOODNESS_TAGS = (
    "int_err",
    "slope",
    "outlier",
    "curvature",
    "rsquared",
    "signal_to_blank",
    "signal_to_baseline",
    "smart_filter",
)
GOODNESS_NAMES = (
    "Intercept Error",
    "Slope",
    "Outliers",
    "Curvature",
    "RSquared",
    "Blank/Signal %",
    "Baseline/Signal %",
    "Smart Filter",
)
INVERTED_GOODNESS = ("rsquared",)

ISO_EVO_RESULT_ARGS = (
    "intercept_value",
    "intercept_error",
    "normalized_error",
    "slope",
    "outlier",
    "curvature",
    "rsquared",
)


class IsoEvoResult(BaseResult):
    isotope_obj = None
    n = Str
    fit = Str
    intercept_value = Float
    intercept_error = Float
    percent_error = Float
    regression_str = Str
    int_err_goodness = None
    slope_goodness = None
    outlier_goodness = None
    curvature_goodness = None
    rsquared_goodness = None
    signal_to_blank_goodness = None
    signal_to_baseline_goodness = None
    smart_filter_goodness = None

    int_err_threshold = None
    slope_threshold = None
    outlier_threshold = None
    curvature_threshold = None
    rsquared_threshold = None
    signal_to_blank_threshold = None
    signal_to_baseline_threshold = None
    signal_to_baseline_percent_threshold = None
    smart_filter_threshold = None

    int_err = None
    slope = None
    outlier = None
    curvature = None
    rsquared = None
    normalized_err = None
    signal_to_blank = None
    signal_to_baseline = None
    smart_filter = None

    hover_text = Property

    klass = None

    @cached_property
    def _get_hover_text(self):
        a = "RunID: {}".format(self.record_id)
        lines = [a]
        return lines

    @property
    def goodness(self):
        good = True
        for g in GOODNESS_TAGS:
            v = getattr(self, "{}_goodness".format(g))
            if v is not None:
                good &= v

        return good

    @property
    def tooltip(self):
        def f(t, m):
            g = getattr(self, "{}_goodness".format(t))
            v = getattr(self, t)
            th = getattr(self, "{}_threshold".format(t))
            if g is not None:
                comp = "<" if t in INVERTED_GOODNESS else ">"
                g = "OK" if g else "Bad {}{}{}".format(floatfmt(v, n=4), comp, th)
            else:
                g = "Not Tested"

            return "{:<25}: {}".format(m, g)

        return "\n".join([f(g, n) for g, n in zip(GOODNESS_TAGS, GOODNESS_NAMES)])


# ============= EOF =============================================
