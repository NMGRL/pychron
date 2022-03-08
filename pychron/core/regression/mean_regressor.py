# ===============================================================================
# Copyright 2012 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================

from numpy import average, where, full

from pychron.core.helpers.formatting import floatfmt
from pychron.pychron_constants import SEM, MSEM
from .base_regressor import BaseRegressor


class MeanRegressor(BaseRegressor):
    _fit = "average"

    def get_exog(self, pts):
        return pts

    def fast_predict2(self, endog, exog):
        return full(exog.shape[0], endog.mean())

    def calculate(self, filtering=False, **kw):
        # cxs, cys = self.pre_clean_ys, self.pre_clean_ys
        if not filtering:
            # prevent infinite recursion
            self.calculate_filtered_data()

    def calculate_outliers(self):
        nsigma = self.filter_outliers_dict.get("std_devs", 2)
        res = abs(self.ys - self.mean)
        s = self.std
        self.filter_bound_value = s * nsigma
        return where(res >= (s * nsigma))[0]

    def _calculate_coefficients(self):
        ys = self.clean_ys
        if self._check_integrity(ys, ys):
            return [ys.mean()]
        else:
            return 0

    def _calculate_coefficient_errors(self):
        return [self.std, self.sem]

    @property
    def summary(self):

        m = self.mean
        e = self.std
        sem = self.sem
        return """mean={}
std={}
sem={}

""".format(
            m, e, sem
        )

    def predict(self, xs=None, *args):
        if xs is not None:
            if isinstance(xs, (float, int)):
                return self.mean

            if isinstance(xs, (list, tuple)):
                n = len(xs)
            else:
                n = xs.shape[0]

            return full(n, self.mean)
        else:
            return self.mean

    def calculate_ci(self, fx, fy):
        #         c = self.predict(fx)
        # fit = self.fit.lower()
        # ec = 'sem' if fit.endswith('sem') else 'sd'
        e = self.predict_error(fx)
        ly = fy - e
        uy = fy + e
        return ly, uy

    def tostring(self, sig_figs=3):

        m = self.mean
        std = self.std
        sem = self.sem
        se = self.se

        sm = floatfmt(m, n=9)
        sstd = floatfmt(std, n=9)
        ssem = floatfmt(sem, n=9)
        sse = floatfmt(se, n=9)

        pstd = self.format_percent_error(m, std)
        psem = self.format_percent_error(m, sem)
        pse = self.format_percent_error(m, se)

        n = self.n
        tn = self.xs.shape[0]
        s = "mean={}, n={}({}), std={} ({}), sem={} ({}) se={} ({})".format(
            sm, n, tn, sstd, pstd, ssem, psem, sse, pse
        )
        # s = fmt.format(m, std, self.percent_error(m, std),
        #                sem, self.percent_error(m, sem))
        return s

    def make_equation(self):
        return "Mean"

    def predict_error(self, x, error_calc=None):
        if error_calc is None:
            error_calc = self.error_calc_type
            if not error_calc:
                error_calc = "SEM" if "sem" in self.fit.lower() else "SD"

        error_calc = error_calc.lower()
        if error_calc == SEM.lower():
            e = self.sem
        elif error_calc in (MSEM.lower(), "msem"):
            e = self.se * (self.mswd**0.5 if self.mswd > 1 else 1)
        else:
            e = self.std

        if isinstance(x, (float, int)):
            return e
        else:
            if isinstance(x, (list, tuple)):
                n = len(x)
            else:
                n = x.shape[0]

            return full(n, e)

    def calculate_standard_error_fit(self):
        return self.std

    def _check_integrity(self, x, y):
        nx, ny = x.shape[0], y.shape[0]
        if not nx or not ny:
            return
        if nx != ny:
            return

        return True


class WeightedMeanRegressor(MeanRegressor):
    def fast_predict2(self, endog, exog):
        # ws = 1 / self.clean_yserr ** 2
        ws = self._get_weights()
        mean = average(endog, weights=ws)
        return full(exog.shape[0], mean)

    @property
    def se(self):
        """
        aka Taylor error, aka standard error of the weighted mean
        :return:
        """
        ws = self._get_weights()
        return sum(ws) ** -0.5

    @property
    def mean(self):
        ys = self.clean_ys
        ws = self._get_weights()
        if self._check_integrity(ys, ws):
            return average(ys, weights=ws)
        else:
            return average(ys)

    # @property
    # def mean_std(self):
    #     if len(self.weights):
    #         var = 1 / sum(self.weights)
    #         return var ** 0.5

    def _get_weights(self):
        e = self.clean_yserr
        if self._check_integrity(e, e):
            return 1 / e**2


# ============= EOF =============================================
