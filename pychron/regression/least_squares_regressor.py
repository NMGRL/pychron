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
from traits.api import Callable, List
from pychron.regression.base_regressor import BaseRegressor
#============= standard library imports ========================
from scipy import optimize
from numpy import asarray, sqrt, matrix, diagonal, array
#============= local library imports  ==========================
import re
from pychron.helpers.formatting import floatfmt
class LeastSquaresRegressor(BaseRegressor):
    fitfunc = Callable
    initial_guess = List
    def make_equation(self):
        import inspect
        eq = inspect.getsource(self.fitfunc).strip()

        def func(match):
            m = match.group(0)
            idx = int(m[2:-1])
            return floatfmt(self._coefficients[idx])

        for ci in self._coefficients:
            eq = re.sub(r'p\[\d]', func, eq)

        h, t = eq.split(':')
        return 'fitfunc={}'.format(t)

    def _fitfunc_changed(self):
        self.calculate()
#
    def _initial_guess_changed(self):
        self._degree = len(self.initial_guess) - 1
#         self.calculate()
#
#    def _errfunc_changed(self):
#        self.calculate()
#
    def calculate(self):
        if not len(self.xs) or \
            not len(self.ys):
            return

        if len(self.xs) != len(self.ys):
            return

        if self.fitfunc and \
            self.initial_guess is not None and \
                 len(self.initial_guess) and \
                    len(self.xs) >= len(self.initial_guess):
            errfunc = lambda p, x, v: self.fitfunc(p, x) - v
            r = optimize.leastsq(errfunc,
                                 self.initial_guess,
                                 args=(self.xs, self.ys), full_output=True)

#            r = optimize.curve_fit(self.fitfunc,
#                                   self.xs, self.ys,
#                                   p0=self.initial_guess)
            if r:
                coeffs, cov, _infodict, _msg, _ier = r
#                print r, self.initial_guess
                self._coefficients = list(coeffs)
                self._covariance = cov

                self._coefficient_errors = list(sqrt(diagonal(cov)))

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

        fx = self.fitfunc(self._coefficients, x)
        if return_single:
            fx = fx[0]

        return fx

    def predict_error(self, x, ys, error_calc='sem'):

        '''
            returns percent error
        '''
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
        fx = ys * fx / 100.

        if return_single:
            fx = fx[0]

        return fx

#============= EOF =============================================
