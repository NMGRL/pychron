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
from traits.api import Array
#============= standard library imports ========================
from numpy import average, ones, asarray
#============= local library imports  ==========================
from base_regressor import BaseRegressor

class MeanRegressor(BaseRegressor):
    ddof = 1
    _fit = 'average'
    def _calculate_coefficients(self):
        if len(self.ys):
            return [self.ys.mean()]
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
        if len(self.ys):
            return self.ys.mean()
        else:
            return 0

    @property
    def std(self):
        """
            mass spec uses ddof=1
            ddof=0 provides a maximum likelihood estimate of the variance for normally distributed variables
            ddof=1 unbiased estimator of the variance of the infinite population
        """
        if len(self.ys):
            # ys = asarray(self.ys, dtype=float64)
            return self.ys.std(ddof=self.ddof)
        else:
            return 0

    @property
    def sem(self):
        if len(self.ys):
            return self.std * 1 / len(self.ys) ** 0.5
        else:
            return 0

    def predict(self, xs, *args):
        return ones(asarray(xs).shape) * self.mean

    def calculate_ci(self, fx, fy):
#         c = self.predict(fx)
        fit = self.fit.lower()
        ec = 'sem' if fit.endswith('sem') else 'sd'
        e = self.predict_error(fx, error_calc=ec)
        ly = fy - e
        uy = fy + e
        return ly, uy

    def tostring(self, sig_figs=5, error_sig_figs=5):
        fmt = 'mean={{}} std={{:0.{}f}} ({{:0.2f}}%), sem={{:0.{}f}} ({{:0.2f}}%)'.format(sig_figs, error_sig_figs)

        m = self.mean
        std = self.std
        sem = self.sem
        s = fmt.format(m, std, self.percent_error(m, std),
                       sem, self.percent_error(m, sem)
                       )
        return s

    def make_equation(self):
        return

    def predict_error(self, x, error_calc='sem'):
        if error_calc == 'sem':
            e = self.sem
        else:
            e = self.std
        return ones(asarray(x).shape) * e

    def calculate_standard_error_fit(self):
        return self.std

class WeightedMeanRegressor(MeanRegressor):
    errors = Array
    @property
    def mean(self):
        return average(self.ys, weights=self.weights)

    @property
    def std(self):
        var = 1 / sum(self.weights)
        return var ** 0.5

    @property
    def weights(self):
        return 1 / self.errors ** 2


#============= EOF =============================================
