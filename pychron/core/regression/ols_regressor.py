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

from traits.api import Int, Property
# ============= standard library imports ========================
from numpy import asarray, column_stack, ones, \
    matrix, sqrt, dot, linalg, zeros_like, hstack

from statsmodels.api import OLS
# try:
#
# except ImportError:
#     try:
#         from scikits.statsmodels.api import OLS
#     except ImportError:
#         from pyface.message_dialog import warning
#
#         warning(None, 'statsmodels is required but was not found')

import logging

logger = logging.getLogger('Regressor')

# ============= local library imports  ==========================
from base_regressor import BaseRegressor


class OLSRegressor(BaseRegressor):
    degree = Property(depends_on='_degree')
    _degree = Int
    constant = None
    _ols = None

    def set_degree(self, d, refresh=True):
        if isinstance(d, str):
            d = d.lower()
            fits = ['linear', 'parabolic', 'cubic']
            if d in fits:
                d = fits.index(d) + 1
            else:
                d = None

        if d is None:
            d = 1

        self._degree = d
        if refresh:
            self.dirty = True

    def get_exog(self, x):
        return self._get_X(x)

    def fast_predict(self, endog, exog):
        ols = self._ols
        ols.wendog = ols.whiten(endog)
        result = ols.fit()
        return result.predict(exog)

    def fast_predict2(self, endog, exog):
        """
        this function is less flexible than fast_predict but is 2x faster. it doesn't use RegressionResults class
        simple does the lin algebra to predict values.

        currently useful for monte_carlo_estimation
        """
        if not hasattr(self, 'pinv_wexog'):
            self.pinv_wexog = linalg.pinv(self._ols.wexog)
        beta = dot(self.pinv_wexog, endog)

        return dot(exog, beta)

    def calculate(self, filtering=False):
        cxs = self.pre_clean_xs
        cys = self.pre_clean_ys

        integrity_check = True
        if not self._check_integrity(cxs, cys):
            if len(cxs) == 1 and len(cys) == 1:
                cxs = hstack((cxs, cxs[0]))
                cys = hstack((cys, cys[0]))
                integrity_check = False
                # cys.append(cys[0])
            else:
                self._result = None
                # logger.debug('A integrity check failed')
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
                logger.debug('B integrity check failed')
                # self.debug('B integrity check failed')
                return

            try:
                ols = self._engine_factory(fy, X, check_integrity=integrity_check)
                self._ols = ols
                self._result = ols.fit()

            except Exception, e:
                import traceback

                traceback.print_exc()

    def calculate_error_envelope2(self, fx, fy):
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

        if error_calc == 'CI':
            e = self.calculate_ci_error(x)
        else:
            e = self.predict_error_matrix(x, error_calc)

        if return_single:
            e = e[0]
        return e

    def predict_error_algebraic(self, x, error_calc='sem'):
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
            if error_calc == 'sem':
                var_Ypred = s * s * a
            else:
                var_Ypred = s * s * (1 + a)

            return sqrt(var_Ypred)

        return [calc_error(xi) for xi in x]

    def predict_error_matrix(self, x, error_calc='SEM'):
        """
            predict the error in y using matrix math
            draper and smith chapter 2.4 page 56

            Xk'=(1, x, x**2...x)

        """
        x = asarray(x)
        sef = self.calculate_standard_error_fit()

        def calc_hat(xi):
            Xk = self._get_X(xi).T

            covarM = matrix(self.var_covar)
            varY_hat = (Xk.T * covarM * Xk)

            return varY_hat[0, 0]

        if error_calc == 'SEM':
            def func(xi):
                varY_hat = calc_hat(xi)
                return sef * sqrt(varY_hat)
        elif error_calc == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
            mswd = self.mswd

            def func(xi):
                varY_hat = calc_hat(xi)
                m = mswd ** 0.5 if mswd > 1 else 1
                return sef * sqrt(varY_hat) * m
        else:
            def func(xi):
                varY_hat = calc_hat(xi)
                return sqrt(sef ** 2 + sef ** 2 * varY_hat)

        if not self._result:
            return zeros_like(x)
        else:
            return [func(xi) for xi in x]
            # func = calc_sem if error_calc == 'SEM' else calc_sd
            # return [func(xi) for xi in x]

    def predict_error_al(self, x, error_calc='sem'):
        """
            predict error in y using MassSpec Algorithm

            only here for verification

        """
        cov_varM = matrix(self.var_covar)
        se = self.calculate_standard_error_fit()

        def predict_yi_err(xi):
            """
                bx= x**0,x**1,x**n where n= degree of fit linear=2, parabolic=3 etc
            """
            bx = asarray([pow(xi, i) for i in range(self.degree + 1)])
            bx_covar = bx * cov_varM
            bx_covar = asarray(bx_covar)[0]
            var = sum(bx * bx_covar)
            #            print var
            s = se * var ** 0.5
            if error_calc == 'sd':
                s = (se ** 2 + s ** 2) ** 0.5

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
        fits = ['linear', 'parabolic', 'cubic']
        return fits[self._degree - 1]

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
        X = column_stack(cols)
        return X

        # @cached_property
        # def _get_mswd(self):
        #     self.valid_mswd = False
        #     if self._degree == 1:
        #         # a = self.intercept
        #         # b = self.slope
        #         coeffs = self._calculate_coefficients()
        #         if not len(coeffs):
        #             self.calculate()
        #             coeffs = self._calculate_coefficients()
        #
        #         if len(coeffs):
        #             # x = self.xs
        #             # y = self.ys
        #             #
        #             # sx = self.xserr
        #             # sy = self.yserr
        #
        #             # if not len(sx):
        #             #     sx=zeros(self.n)
        #             # if not len(sy):
        #             #     sy=zeros(self.n)
        #
        #             # x=self._clean_array(x)
        #             # y=self._clean_array(y)
        #             # sx=self._clean_array(sx)
        #             # sy=self._clean_array(sy)
        #             x, y, sx, sy = self.clean_xs, self.clean_ys, self.clean_xserr, self.clean_yserr
        #             if self._check_integrity(x, y) and \
        #                     self._check_integrity(x, sx) and \
        #                     self._check_integrity(x, sy):
        #                 m = calculate_mswd2(x, y, sx, sy, coeffs[1], coeffs[0])
        #                 self.valid_mswd = validate_mswd(m, len(ys), k=2)
        #                 return m
        #             else:
        #                 return 'NaN'
        #         else:
        #             return 'NaN'
        #     else:
        #         return super(OLSRegressor, self)._get_mswd()


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

    def _get_X(self, xs=None):
        if xs is None:
            xs = self.clean_xs

        r, c = xs.shape
        if c == 2:
            xs = column_stack((xs, ones(r)))
            return xs

            # def predict_error_matrix(self, x, error_calc=None):
            #     """
            #         predict the error in y using matrix math
            #         draper and smith chapter 2.4 page 56
            #
            #         Xk'=(1, x, x**2...x)
            #     """
            #     if error_calc is None:
            #         error_calc=self.error_calc_type
            #
            #     def calc_error(xi, sef):
            #         Xk = self._get_X(xi).T
            #         # Xk=column_stack((xs/, ones(r)))
            #         covarM = matrix(self.var_covar)
            #         varY_hat = (Xk.T * covarM * Xk)
            #         # print varY_hat
            #         # varY_hat = sum(diag(varY_hat))
            #         if error_calc == 'SEM':
            #             se = sef * sqrt(varY_hat)
            #         else:
            #             se = sqrt(sef ** 2 + sef ** 2 * varY_hat)
            #
            #         return se
            #
            #     sef = self.calculate_standard_error_fit()
            #     return [calc_error(xi, sef) for xi in asarray(x)]


if __name__ == '__main__':
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
    r = MultipleLinearRegressor(xs=xs, ys=ys, fit='linear')
    print r.predict([(0, 1)])
    print r.predict_error([(0, 2)])
    print r.predict_error([(0.1, 1)])
# ============= EOF =============================================
# def predict_error_al(self, x, error_calc='sem'):
#        result = self._result
#        cov_varM = result.cov_params()
#        cov_varM = matrix(cov_varM)
#        se = self.calculate_standard_error_fit()
#
#        def predict_yi_err(xi):
#            '''
#
#                bx= x**0,x**1,x**n where n= degree of fit linear=2, parabolic=3 etc
#
#            '''
#            bx = asarray([pow(xi, i) for i in range(self.degree + 1)])
#            bx_covar = bx * cov_varM
#            bx_covar = asarray(bx_covar)[0]
#            var = sum(bx * bx_covar)
# #            print var
#            s = var ** 0.5
#            if error_calc == 'sd':
#                s = (se ** 2 + s ** 2) ** 2
#
#            return s
#
#        if isinstance(x, (float, int)):
#            x = [x]
#        x = asarray(x)
#
#        return [predict_yi_err(xi) for xi in x]
