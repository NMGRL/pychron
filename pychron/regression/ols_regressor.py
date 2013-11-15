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
from numpy.lib.twodim_base import diag
#============= enthought library imports =======================
from traits.api import Int, Property
#============= standard library imports ========================
from numpy import polyval, asarray, column_stack, ones, \
    matrix, sqrt, abs


try:
    from statsmodels.api import OLS
except ImportError:
    from scikits.statsmodels.api import OLS

#============= local library imports  ==========================
from base_regressor import BaseRegressor


class OLSRegressor(BaseRegressor):
    degree = Property(depends_on='_degree')
    _degree = Int
    constant = None
    #    _result = None
    #    @on_trait_change('xs,ys')
    #    def _update_data(self):
    #        self._ols = OLS(self.xs, vander(self.ys, self.degree + 1))
    #        self._result = self._ols.fit()
    #    def _xs_changed(self):
    #            xs = asarray(self.xs)
    #            ys = asarray(self.ys)
    # #            print len(xs), len(ys)
    #            self._ols = OLS(ys, vander(xs, self.degree + 1))
    #            self._result = self._ols.fit()
    def __degree_changed(self):
        if self._degree:
            self.calculate()

    def calculate(self):
        """
            vander is equivalent to sm.add_constant(np.column_stack((x**n,..x**2,x**1)))
            vander(x,n+1)
        """

        if not len(self.xs) or \
                not len(self.ys):
            return

        if len(self.xs) != len(self.ys):
            return

        #        xs = asarray(self.xs)
        ys = asarray(self.ys)
        #        self._ols = OLS(ys, vander(xs, self.degree + 1))
        #        self._result = self._ols.fit()
        #            print len(xs), len(ys)
        #        print self.degree
        #        print vander(xs, self.degree + 1)
        X = self._get_X()
        if X is not None:
            try:
            #                 print ys
            #                 print X
                ols = OLS(ys, X)
                self._result = ols.fit()
            except Exception, e:
                print 'calculate', e
                #                print 'X', X
                #                print 'ys', ys
                #        print self.degree, self._result.summary()

    def predict(self, pos):
        return_single = False
        if isinstance(pos, (float, int)):
            return_single = True
            pos = [pos]

        pos = asarray(pos)

        X = self._get_X(xs=pos)
        res = self._result

        if res:
            pred = res.predict(X)
            if return_single:
                pred = pred[0]
            return pred
            #                return self._result.predict(X)[0]

    def predict_error(self, x, error_calc='sem'):
        return_single = False
        if isinstance(x, (float, int)):
            x = [x]
            return_single = True

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

    def predict_error_matrix(self, x, error_calc='sem'):
        '''
            predict the error in y using matrix math
            draper and smith chapter 2.4 page 56
        '''
        '''
            Xk'=(1, x, x**2...x)
            
        '''
        #        if isinstance(x, (float, int)):
        #            x = [x]

        x = asarray(x)
        sef = self.calculate_standard_error_fit()

        def calc_error(xi, se):

            Xk = matrix([pow(xi, i) for i in range(self.degree + 1)]).T
            covarM = matrix(self.var_covar)
            varY_hat = (Xk.T * covarM * Xk)
            varY_hat = varY_hat[0, 0]

            if error_calc == 'sem':
                se = se * sqrt(varY_hat)
            else:
                se = sqrt(se ** 2 + se ** 2 * varY_hat)

            return se

        return [calc_error(xi, sef) for xi in x]

    def predict_error_al(self, x, error_calc='sem'):
        '''
            predict error in y using MassSpec Algorithm
            
            only here for verification
            
        '''
        cov_varM = matrix(self.var_covar)
        se = self.calculate_standard_error_fit()

        def predict_yi_err(xi):
            '''
                
                bx= x**0,x**1,x**n where n= degree of fit linear=2, parabolic=3 etc
                
            '''
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

    #    def calculate_var_covar(self):
    #        '''
    #            return (X'X)^-1
    #        '''
    #        xs = self.xs
    #        n = float(xs.shape[0])
    #        xm = xs.mean()
    #        ssx = self.ssx
    #
    #        a = (xs ** 2).sum() / (n * ssx)
    #        b = -xm / (ssx)
    #        c = 1 / ssx
    #        v = matrix([[a, b], [b, c]])
    #        return v

    #    def calculate_var_covar(self):
    #        X = matrix(self._get_X())
    #        v = X.T * X
    #        v = v.I
    #        return v

    #    def _calculate_X(self):

    def calculate_y(self, x):
        coeffs = self.coefficients
        return polyval(coeffs, x)

    def calculate_yerr(self, x):
        if abs(x) < 1e-14:
            return self.coefficient_errors[0]
        return

    def calculate_x(self, y):
        return 0

    #    def calculate_standard_error_fit(self):
    #        res = self.calculate_residuals()
    #        ss_res = (res ** 2).sum()
    # #        s = std(devs)
    # #        s = (dd.sum() / (devs.shape[0])) ** 0.5
    #
    #        '''
    #            mass spec calculates error in fit as
    #            see LeastSquares.CalcResidualsAndFitError
    #
    #            SigmaFit=Sqrt(SumSqResid/((NP-1)-(q-1)))
    #
    #            NP = number of points
    #            q= number of fit params... parabolic =3
    #        '''
    #        n = res.shape[0]
    #        q = self._degree
    #        s = (ss_res / (n - 1 - q)) ** 0.5
    #        return s

    def _calculate_coefficients(self):
        '''
            params = [a,b,c]
            where y=ax**2+bx+c
        '''
        if self._result:

        #            print 'dsaffsadf', self._result.params
            return self._result.params
            #        return polyfit(self.xs, self.ys, self.degree)

    def _calculate_coefficient_errors(self):
        if self._result:
        #            result = self._result
        #            covar_diag = result.cov_params().diagonal()
        #            n = result.nobs
        #            q = result.df_model
        #            ssr = result.ssr
        #            sigma_fit = (ssr / ((n - 1) - q)) ** 0.5
        #            errors = sigma_fit * covar_diag
        #            print errors, self._result.bse
            return self._result.bse

            #    def _calculate_confidence_interval(self, x):
            #        return self._result.conf_int


    def _get_degree(self):
        return self._degree

    def _set_degree(self, d):
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
        self.dirty = True

    @property
    def summary(self):
        return self._result.summary()

    @property
    def var_covar(self):
        return self._result.normalized_cov_params

    #    @property
    #    def fit(self):
    #        fits = ['linear', 'parabolic', 'cubic']
    #        return fits[self._degree - 1]

    def _get_fit(self):
        fits = ['linear', 'parabolic', 'cubic']
        return fits[self._degree - 1]

    #        return self._fit

    def _set_fit(self, v):
        self._set_degree(v)

    #        self._fit = v

    def _get_X(self, xs=None):
        if xs is None:
            xs = asarray(self.xs)

        '''
            returns X matrix
            X=[[1,xi,xi^2,...]
                .
                .
                .
                [1,xj,xj^2,...]
                ]
        '''
        #        xs = self.xs
        cols = [pow(xs, i) for i in range(self.degree + 1)]
        X = column_stack(cols)
        return X

#        return asarray(self._calculate_X())
#        X = vander(xs, self.degree + 1)
#        if self.constant:
#            c[:, self.degree] *= self.constant
#        X = add_constant(xs)
#        return X

class PolynomialRegressor(OLSRegressor):
    pass


class MultipleLinearRegressor(OLSRegressor):
    '''
        xs=[(x1,y1),(x2,y2),...,(xn,yn)]
        ys=[z1,z2,z3,...,zn]
        
        if you have a list of x's and y's 
        X=array(zip(x,y))
        if you have a tuple of x,y pairs
        X=array(xy)
    '''


    def _get_X(self, xs=None):
        if xs is None:
            xs = self.xs

        xs = asarray(xs)

        r, c = xs.shape
        if c == 2:
            x1, x2 = xs.T
            xs = column_stack((xs, ones(r)))
            return xs

    def predict_error_matrix(self, x, error_calc='sem'):
        '''
            predict the error in y using matrix math
            draper and smith chapter 2.4 page 56
        '''
        '''
            Xk'=(1, x, x**2...x)
            
        '''
        #        if isinstance(x, (float, int)):
        #            x = [x]

        x = asarray(x)
        sef = self.calculate_standard_error_fit()

        def calc_error(xi, se):
            #xi = hstack((xi, (1,)))
            #            print xi, pow(xi, 3), 'ff'
            #            print self.degree
            #            print range(self.degree + 1)
            #            print [pow(xi, i) for i in range(self.degree + 1)]
            #Xk = matrix([pow(xi, i) for i in range(self.degree + 1)]).T
            Xk = self._get_X(xi).T

            covarM = matrix(self.var_covar)
            varY_hat = (Xk.T * covarM * Xk)
            varY_hat = sum(diag(varY_hat))
            #            print varY_hat
            #
            if error_calc == 'sem':
                se = sef * sqrt(varY_hat)
            else:
                se = sqrt(sef ** 2 + sef ** 2 * varY_hat)

            return se

        return [calc_error(xi, sef) for xi in x]



        #def predict_error_matrix(self, x, error_calc='sem'):
        #    '''
        #        predict the error in y using matrix math
        #        draper and smith chapter 2.4 page 56
        #    '''
        #    '''
        #        Xk'=(1, x, x**2...x)
        #
        #    '''
        #    #        if isinstance(x, (float, int)):
        #    #            x = [x]
        #
        #    x = asarray(x)
        #    sef = self.calculate_standard_error_fit()
        #
        #    def calc_error(xi, se):
        #        #xi = hstack((xi, (1,)))
        #        #            print xi, pow(xi, 3), 'ff'
        #        #            print self.degree
        #        #            print range(self.degree + 1)
        #        #            print [pow(xi, i) for i in range(self.degree + 1)]
        #        #Xk = matrix([pow(xi, i) for i in range(self.degree + 1)]).T
        #
        #        #xs = asarray(xi)
        #        #x1, x2 = xs.T
        #
        #        #Xk = column_stack((x1, x2, x1 ** 2, x2 ** 2, x1 * x2, ones_like(x1))).T
        #        Xk=self._get_X(xi).T
        #        covarM = matrix(self.var_covar)
        #        varY_hat = (Xk.T * covarM * Xk)
        #        varY_hat = sum(diag(varY_hat))
        #        #            print varY_hat
        #        #
        #        if error_calc == 'sem':
        #            se = sef * sqrt(varY_hat)
        #        else:
        #            se = sqrt(sef ** 2 + sef ** 2 * varY_hat)
        #
        #        return se
        #
        #    return [calc_error(xi, sef) for xi in x]


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
#============= EOF =============================================
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
