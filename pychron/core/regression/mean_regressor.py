#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
from numpy import average, ones, asarray, where
#============= local library imports  ==========================
from base_regressor import BaseRegressor
from pychron.core.helpers.formatting import floatfmt


class MeanRegressor(BaseRegressor):
    ddof = 1
    _fit = 'average'

    def calculate(self, filtering=False, **kw):
        # cxs, cys = self.pre_clean_ys, self.pre_clean_ys
        if not filtering:
            #prevent infinite recursion
            self.calculate_filtered_data()

    def calculate_outliers(self, nsigma=2):
        res = abs(self.ys - self.mean)
        s = self.std
        return where(res > (s * nsigma))[0]

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
        return '''mean={}
std={}
sem={}

'''.format(m, e, sem)

    @property
    def mean(self):
        ys = self.clean_ys
        if self._check_integrity(ys, ys):
            return ys.mean()
        else:
            return 0

    @property
    def std(self):
        """
            mass spec uses ddof=1
            ddof=0 provides a maximum likelihood estimate of the variance for normally distributed variables
            ddof=1 unbiased estimator of the variance of the infinite population
        """
        ys = self.clean_ys
        if len(ys) > self.ddof:
            # ys = asarray(self.ys, dtype=float64)
            return ys.std(ddof=self.ddof)
        else:
            return 0

    @property
    def sem(self):
        ys = self.clean_ys
        if self._check_integrity(ys, ys):
            n = len(ys) - self.ddof
            if n > 0:
                return self.std * n ** -0.5
            else:
                return 0
        else:
            return 0

    def predict(self, xs=None, *args):
        if xs is not None:
            return ones(asarray(xs).shape) * self.mean
        else:
            return self.mean

    def calculate_ci(self, fx, fy):
        #         c = self.predict(fx)
        #fit = self.fit.lower()
        #ec = 'sem' if fit.endswith('sem') else 'sd'
        e = self.predict_error(fx)
        ly = fy - e
        uy = fy + e
        return ly, uy

    def tostring(self, sig_figs=3, error_sig_figs=4):
        # fmt = 'mean={{}} std={{:0.{}f}} ({{:0.2f}}%), sem={{:0.{}f}} ({{:0.2f}}%)'.format(sig_figs, error_sig_figs)

        m = self.mean
        std = self.std
        sem = self.sem

        sm = floatfmt(m, n=3)
        sstd = floatfmt(std, n=4)
        ssem = floatfmt(sem, n=4)

        pstd = self.format_percent_error(m, std)
        psem = self.format_percent_error(m, sem)

        s = 'mean={}, std={} ({}), sem={} ({})'.format(sm, sstd, pstd, ssem, psem)
        # s = fmt.format(m, std, self.percent_error(m, std),
        #                sem, self.percent_error(m, sem))
        return s

    def make_equation(self):
        return

    def predict_error(self, x, error_calc=None):
        if error_calc is None:
            error_calc = self.error_calc_type
            if not error_calc:
                error_calc = 'SEM' if 'sem' in self.fit.lower() else 'SD'

        if error_calc == 'SEM':
            e = self.sem
        elif error_calc == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
            e = self.sem * (self.mswd ** 0.5 if self.mswd > 1 else 1)
        else:
            e = self.std

        return ones(asarray(x).shape) * e

    def calculate_standard_error_fit(self):
        return self.std

    def _check_integrity(self, x, y):
        nx, ny = len(x), len(y)
        if not nx or not ny:
            return
        if nx != ny:
            return

        return True


class WeightedMeanRegressor(MeanRegressor):
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
            return 1 / e ** 2


#============= EOF =============================================
