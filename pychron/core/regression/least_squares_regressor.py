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

from numpy import asarray, sqrt, matrix, diagonal, array, exp
# ============= standard library imports ========================
from scipy import optimize
from traits.api import Callable, List

from pychron.core.regression.base_regressor import BaseRegressor


# ============= local library imports  ==========================


class FitError(BaseException):
    pass


class LeastSquaresRegressor(BaseRegressor):
    fitfunc = Callable
    initial_guess = List

    _covariance = None

    # def make_equation(self):
    #     import inspect
    #     eq = inspect.getsource(self.fitfunc).strip()
    #
    #     def func(match):
    #         m = match.group(0)
    #         idx = int(m[2:-1])
    #         return floatfmt(self._coefficients[idx])
    #
    #     for ci in self._coefficients:
    #         eq = re.sub(r'p\[\d]', func, eq)
    #
    #     h, t = eq.split(':')
    #     return 'fitfunc={}'.format(t)

    # def _fitfunc_changed(self):
    #     self.calculate()

    # def _initial_guess_changed(self):
    #     self._degree = len(self.initial_guess) - 1

    def calculate(self, filtering=False):
        cxs = self.pre_clean_xs
        cys = self.pre_clean_ys

        if not self._check_integrity(cxs, cys):
            # logger.debug('A integrity check failed')
            # import traceback
            # traceback.print_stack()
            return

        if not filtering:
            # prevent infinite recursion
            fx, fy = self.calculate_filtered_data()
        else:
            fx, fy = cxs, cys
        try:
            coeffs, cov = optimize.curve_fit(self.fitfunc, fx, fy, p0=self._calculate_initial_guess())
            self._coefficients = list(coeffs)
            self._covariance = cov
            self._coefficient_errors = list(sqrt(diagonal(cov)))
        except RuntimeError:
            from pyface.message_dialog import warning
            warning(None, 'Exponential failed to converge. Choose a different fit')
            raise FitError()

    def _calculate_coefficients(self):
        return self._coefficients

    def _calculate_coefficient_errors(self):
        return self._coefficient_errors

    def predict(self, x):
        return_single = False
        if not hasattr(x, '__iter__'):
            x = [x]
            return_single = True

        x = asarray(x)

        fx = self.fitfunc(x, *self._coefficients)
        if return_single:
            fx = fx[0]

        return fx

    def predict_error(self, x, error_calc='sem'):
        """
            returns percent error
        """
        return_single = False
        if not hasattr(x, '__iter__'):
            x = [x]
            return_single = True

        sef = self.calculate_standard_error_fit()
        r, _ = self._covariance.shape

        def calc_error(xi):
            Xk = matrix([xi, ] * r).T

            varY_hat = (Xk.T * self._covariance * Xk)
            if error_calc == 'sem':
                se = sef * sqrt(varY_hat)
            else:
                se = sqrt(sef ** 2 + sef ** 2 * varY_hat)

            return se[0, 0]

        fx = array([calc_error(xi) for xi in x])
        # fx = ys * fx / 100.

        if return_single:
            fx = fx[0]

        return fx


class ExponentialRegressor(LeastSquaresRegressor):
    def __init__(self, *args, **kw):
        def fitfunc(x, a, b, c):
            return a * exp(-b * x) + c

        self.fitfunc = fitfunc
        super(ExponentialRegressor, self).__init__(*args, **kw)

    def _calculate_initial_guess(self):
        if self.ys[0] > self.ys[-1]:
            ig = 100, 0.1, -100
        else:
            ig = -10, 0.1, 10
        return ig
# ============= EOF =============================================
