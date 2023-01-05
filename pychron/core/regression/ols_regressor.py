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
import logging

from numpy import (
    asarray,
    column_stack,
    sqrt,
    dot,
    linalg,
    zeros_like,
    hstack,
    ones_like,
    array,
)
from statsmodels.api import OLS
from traits.api import Int, Property

# ============= local library imports  ==========================
from pychron.core.helpers.fits import FITS, fit_to_degree
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.pychron_constants import MSEM, SEM, AUTO_LINEAR_PARABOLIC

logger = logging.getLogger("Regressor")


class OLSRegressor(BaseRegressor):
    degree = Property(depends_on="_degree")
    _degree = Int
    constant = None
    _ols = None

    def set_degree(self, d, refresh=True):
        if isinstance(d, str):
            self._fit = d
            try:
                d = fit_to_degree(d)
            except ValueError:
                d = 1

        if d is None:
            d = 1

        if refresh:
            self.dirty = True
            self._degree = d
        else:
            self.trait_setq(_degree=d)

    def get_exog(self, x):
        return self._get_X(x)

    def fast_predict(self, endog, pexog, exog=None):
        ols = self._ols
        ols.wendog = ols.whiten(endog)

        if exog is not None:
            ols.wexog = ols.whiten(exog)

            # force recalculation
            del ols.pinv_wexog

        result = ols.fit()
        return result.predict(pexog)

    def fast_predict2(self, endog, exog):
        """
        this function is less flexible than fast_predict but is 2x faster. it doesn't use RegressionResults class
        simple does the lin algebra to predict values.

        currently useful for monte_carlo_estimation
        """
        if not hasattr(self, "pinv_wexog"):
            self.pinv_wexog = linalg.pinv(self._ols.wexog)
        beta = dot(self.pinv_wexog, endog)

        return dot(exog, beta)

    def determine_fit(self):
        if self._fit == AUTO_LINEAR_PARABOLIC:
            self.set_degree("linear", refresh=False)
            self.calculate()

            linear_r = self.rsquared_adj

            self.set_degree("parabolic", refresh=False)
            self.calculate()
            parabolic_r = self.rsquared_adj

            if linear_r > parabolic_r:
                self.fit = "linear"
                self.set_degree("linear")
            else:
                self.fit = "parabolic"
                self.set_degree("parabolic")

        return self.fit

    def calculate(self, filtering=False):
        cxs = self.clean_xs
        cys = self.clean_ys

        integrity_check = True
        if not self._check_integrity(cxs, cys, verbose=True):
            if len(cxs) == 1 and len(cys) == 1:
                cxs = hstack((cxs, cxs[0]))
                cys = hstack((cys, cys[0]))
                integrity_check = False
                # cys.append(cys[0])
            else:
                self._result = None
                logger.debug("A integrity check failed")
                # import traceback
                # traceback.print_stack()
                return

        if integrity_check:
            if not filtering:
                # prevent infinite recursion
                fx, fy = self.calculate_filtered_data()
            else:
                fx, fy = cxs, cys
        else:
            fx, fy = cxs, cys

        X = self._get_X(fx)

        if X is not None:
            if integrity_check and not self._check_integrity(X, fy):
                self._result = None
                logger.debug("B integrity check failed")
                # self.debug('B integrity check failed')
                return

            # try:
            ols = self._engine_factory(fy, X, check_integrity=integrity_check)
            self._ols = ols
            self._result = ols.fit()
            # except Exception as e:
            #     import traceback
            #
            #     traceback.print_exc()

    def calculate_prediction_envelope(self, fx, fy):
        from statsmodels.sandbox.regression.predstd import wls_prediction_std

        prstd, iv_l, iv_u = wls_prediction_std(self._result)
        return iv_l, iv_u, self._result.model.exog[::, 1]

    def predict(self, pos):
        return_single = False
        if isinstance(pos, (float, int)):
            return_single = True
            pos = [pos]

        pos = asarray(pos)

        x = self._get_X(xs=pos)

        res = self._result
        if res:
            pred = res.predict(x)
            if return_single:
                pred = pred[0]
            return pred
        else:
            if return_single:
                return 0
            else:
                return zeros_like(pos)

    def predict_error(self, x, error_calc=None):
        if error_calc is None:
            error_calc = self.error_calc_type

        return_single = False
        if isinstance(x, (float, int)):
            x = [x]
            return_single = True

        x = asarray(x)

        if not error_calc or error_calc == "CI":
            e = self.calculate_ci_error(x)
        elif error_calc == "MC":
            e = self.calculate_mc_error(x)
        else:
            e = self.predict_error_matrix(x, error_calc)

        if return_single:
            try:
                e = e[0]
            except TypeError:
                e = 0
        return e

    def predict_error_algebraic(self, x, error_calc="SEM"):
        """
        draper and smith 24

        predict error in y using equation 1.4.6 p.22
        """
        s = self.calculate_standard_error_fit()
        xs = self.xs
        Xbar = xs.mean()
        n = float(xs.shape[0])

        def calc_error(Xk):
            a = 1 / n + (Xk - Xbar) ** 2 / ((xs - Xbar) ** 2).sum()
            if error_calc == SEM:
                var_Ypred = s * s * a
            else:
                var_Ypred = s * s * (1 + a)

            return sqrt(var_Ypred)

        return [calc_error(xi) for xi in x]

    def predict_error_matrix(self, x, error_calc="SEM"):
        """
        predict the error in y using matrix math
        draper and smith chapter 2.4 page 56

        Xk'=(1, x, x**2...x)

        """
        x = asarray(x)
        sef = self.calculate_standard_error_fit()

        covarM = array(self.var_covar)

        def calc_hat(xi):
            Xk = self._get_X(xi).T
            varY_hat = Xk.T.dot(covarM).dot(Xk)
            return varY_hat[0, 0]

        error_calc = error_calc.lower()
        if error_calc == SEM.lower():

            def func(xi):
                varY_hat = calc_hat(xi)
                return sef * sqrt(varY_hat)

        elif error_calc == MSEM.lower():
            mswd = self.mswd

            def func(xi):
                varY_hat = calc_hat(xi)
                m = mswd**0.5 if mswd > 1 else 1
                return sef * sqrt(varY_hat) * m

        else:

            def func(xi):
                varY_hat = calc_hat(xi)
                return sqrt(sef**2 + sef**2 * varY_hat)

        if not self._result:
            return zeros_like(x)
        else:
            return [func(xi) for xi in x]
            # func = calc_sem if error_calc == 'SEM' else calc_sd
            # return [func(xi) for xi in x]

    def predict_error_al(self, x, error_calc="sem"):
        """
        predict error in y using MassSpec Algorithm

        only here for verification

        """
        cov_varM = array(self.var_covar)
        se = self.calculate_standard_error_fit()

        def predict_yi_err(xi):
            """
            bx= x**0,x**1,x**n where n= degree of fit linear=2, parabolic=3 etc
            """
            bx = asarray([pow(xi, i) for i in range(self.degree + 1)])
            bx_covar = bx.dot(cov_varM)
            bx_covar = asarray(bx_covar)[0]
            var = sum(bx * bx_covar)
            #            print var
            s = se * var**0.5
            if error_calc == "sd":
                s = (se**2 + s**2) ** 0.5

            return s

        if isinstance(x, (float, int)):
            x = [x]
        x = asarray(x)

        return [predict_yi_err(xi) for xi in x]

        # def calculate_y(self, x):
        #     coeffs = self.coefficients
        #     return polyval(coeffs, x)
        #
        # def calculate_yerr(self, x):
        #     if abs(x) < 1e-14:
        #         return self.coefficient_errors[0]
        #     return

        # def calculate_x(self, y):
        # return 0

    def _get_rsquared(self):
        if self._result:
            return self._result.rsquared

    def _get_rsquared_adj(self):
        if self._result:
            return self._result.rsquared_adj

    def _calculate_coefficients(self):
        """
        params = [c,b,a]
        where y=ax**2+bx+c
        """
        if self._result:
            return self._result.params
        else:
            return [0, 0]

    def _calculate_coefficient_errors(self):
        if self._result:
            return self._result.bse
        else:
            return [0, 0]

    def _engine_factory(self, fy, X, check_integrity=True):
        return OLS(fy, X)

    def _get_degree(self):
        return self._degree

    def _set_degree(self, d):
        self.set_degree(d)

    @property
    def summary(self):
        if self._result:
            return self._result.summary()

    @property
    def var_covar(self):
        if self._result:
            return self._result.normalized_cov_params

    def _get_degrees_of_freedom(self):
        return len(self.coefficients)

    def __degree_changed(self):
        if self._degree:
            self.calculate()

    def _get_fit(self):
        return FITS[self._degree - 1]

    def _set_fit(self, v):
        self._set_degree(v)

    def _get_X(self, xs=None):
        """
        returns X matrix
        X=[[1,xi,xi^2,...]
            .
            .
            .
            [1,xj,xj^2,...]
            ]
        """
        if xs is None:
            xs = self.clean_xs

        cols = [pow(xs, i) for i in range(self.degree + 1)]
        return column_stack(cols)


class PolynomialRegressor(OLSRegressor):
    pass


class MultipleLinearRegressor(OLSRegressor):
    """
    xs=[(x1,y1),(x2,y2),...,(xn,yn)]
    ys=[z1,z2,z3,...,zn]

    if you have a list of x's and y's
    X=array(zip(x,y))
    if you have a tuple of x,y pairs
    X=array(xy)
    """

    def fast_predict2(self, endog, pexog, **kw):
        # OLSRegressor fast_predict2 is not working for multiplelinear regressor
        # use fast_predict instead
        return self.fast_predict(endog, pexog, **kw)

    def _get_X(self, xs=None):
        if xs is None:
            xs = self.clean_xs

        xs = asarray(xs)
        x1, x2 = xs.T
        xs = column_stack((x1, x2, ones_like(x1)))
        return xs


if __name__ == "__main__":
    #    xs = np.linspace(0, 10, 20)
    #    bo = 4
    #    b1 = 3
    #    ei = np.random.rand(len(xs))
    #    ys = bo + b1 * xs + ei
    #    print ys
    #    p = '/Users/ross/Sandbox/61311-36b'
    #    xs, ys = np.loadtxt(p, unpack=True)
    # #    xs, ys = np.loadtxt(p)
    #    m = PolynomialRegressor(xs=xs, ys=ys, degree=2)
    #    print m.calculate_y(0)
    xs = [(0, 0), (1, 0), (2, 0)]
    ys = [0, 1, 2.01]
    r = MultipleLinearRegressor(xs=xs, ys=ys, fit="linear")
    print(r.predict([(0, 1)]))
    print(r.predict_error([(0, 2)]))
    print(r.predict_error([(0.1, 1)]))
# ============= EOF =============================================
