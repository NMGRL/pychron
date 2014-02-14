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
# from traits.api import HasTraits
from pychron.core.ui import set_toolkit
set_toolkit('qt4')
#============= standard library imports ========================
from unittest import TestCase
import numpy as np
#============= local library imports  ==========================
from pychron.core.regression.mean_regressor import WeightedMeanRegressor
from pychron.core.regression.ols_regressor import PolynomialRegressor
from pychron.core.regression.wls_regressor import WeightedPolynomialRegressor
# from pychron.core.regression.york_regressor import YorkRegressor

class WeightedMeanRegressionTest(TestCase):
    def setUp(self):
        n = 1000
        ys = np.ones(n) * 5
        #        es = np.random.rand(n)
        es = np.ones(n)
        ys = np.hstack((ys, [5.1]))
        es = np.hstack((es, [1000]))
        #        print es
        self.reg = WeightedMeanRegressor(ys=ys, errors=es)

#    def testMean(self):
#        m = self.reg.mean
#        self.assertEqual(m, 5)

class RegressionTest(TestCase):
    def setUp(self):
        self.x = np.array([1, 2, 3, 4, 4, 5, 5, 6, 6, 7])
        self.y = np.array([7, 8, 9, 8, 9, 11, 10, 13, 14, 13])

    def testMeans(self):
        xm = self.x.mean()
        ym = self.y.mean()
        self.assertEqual(xm, 4.3)
        self.assertEqual(ym, 10.2)


class CITest(TestCase):
    def setUp(self):
        self.x = np.array([0, 12, 29.5, 43, 53, 62.5, 75.5, 85, 93])
        self.y = np.array([8.98, 8.14, 6.67, 6.08, 5.9, 5.83, 4.68, 4.2, 3.72])

    def testUpper(self):
        reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
        l, u = reg.calculate_ci([0, 10, 100])
        for ui, ti in zip(u, [9.16, 8.56, 3.83]):
            self.assertAlmostEqual(ui, ti, delta=0.01)

    def testLower(self):
        reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
        l, u = reg.calculate_ci([0])

        self.assertAlmostEqual(l[0], 8.25, delta=0.01)

    def testSYX(self):
        reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
        self.assertAlmostEqual(reg.get_syx(), 0.297, delta=0.01)

    def testSSX(self):
        reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
        self.assertAlmostEqual(reg.get_ssx(), 8301.389, delta=0.01)


class WLSRegressionTest(TestCase):
    def setUp(self):
        self.xs = np.linspace(0, 10, 10)
        self.ys = np.random.normal(self.xs, 1)

        '''
            draper and smith p.8
        '''
        self.xs = [35.3, 29.7, 30.8, 58.8, 61.4, 71.3, 74.4, 76.7, 70.7, 57.5,
                   46.4, 28.9, 28.1, 39.1, 46.8, 48.5, 59.3, 70, 70, 74.5, 72.1,
                   58.1, 44.6, 33.4, 28.6
        ]
        self.ys = [10.98, 11.13, 12.51, 8.4, 9.27, 8.73, 6.36, 8.50,
                   7.82, 9.14, 8.24, 12.19, 11.88, 9.57, 10.94, 9.58,
                   10.09, 8.11, 6.83, 8.88, 7.68, 8.47, 8.86, 10.36, 11.08
        ]
        self.es = np.random.normal(1, 0.5, len(self.xs))

        self.slope = -0.0798
        self.intercept = 13.623
        self.Xk = 28.6
        self.ypred_k = 0.3091
        xs = self.xs
        ys = self.ys
        es = self.es
        self.wls = WeightedPolynomialRegressor(xs=xs, ys=ys,
                                               yserr=es, fit='linear')

    def testVarCovar(self):
        wls = self.wls
        cv = wls.var_covar
        print cv
        print wls._result.normalized_cov_params

    #        print wls._result.cov_params()


class OLSRegressionTest(TestCase):
    def setUp(self):
        self.xs = np.linspace(0, 10, 10)
        #        self.ys = np.random.normal(self.xs, 1)
        #        print self.ys
        self.ys = [-1.8593967, 3.15506254, 1.82144207, 4.58729807, 4.95813564,
                   5.71229382, 7.04611731, 8.14459843, 10.27429285, 10.10989719]

        '''
            draper and smith p.8
        '''
        self.xs = [35.3, 29.7, 30.8, 58.8, 61.4, 71.3, 74.4, 76.7, 70.7, 57.5,
                   46.4, 28.9, 28.1, 39.1, 46.8, 48.5, 59.3, 70, 70, 74.5, 72.1,
                   58.1, 44.6, 33.4, 28.6
        ]
        self.ys = [10.98, 11.13, 12.51, 8.4, 9.27, 8.73, 6.36, 8.50,
                   7.82, 9.14, 8.24, 12.19, 11.88, 9.57, 10.94, 9.58,
                   10.09, 8.11, 6.83, 8.88, 7.68, 8.47, 8.86, 10.36, 11.08
        ]

        self.slope = -0.0798
        self.intercept = 13.623
        self.Xk = 28.6
        self.ypred_k = 0.3091
        xs = self.xs
        ys = self.ys
        ols = PolynomialRegressor(xs=xs, ys=ys, fit='linear')

        self.ols = ols

    def testSlope(self):
        ols = self.ols
        b, s = ols.coefficients
        self.assertAlmostEqual(s, self.slope, 4)

    def testIntercept(self):
        ols = self.ols
        b, s = ols.coefficients
        self.assertAlmostEqual(b, self.intercept, 4)
        self.assertAlmostEqual(ols.predict(0), self.intercept, 4)

    def testPredictYerr(self):
        ols = self.ols
        ypred = ols.predict_error(self.Xk, error_calc='SEM')
        self.assertAlmostEqual(ypred, self.ypred_k, 3)

    def testPredictYerr_matrix(self):
        ols = self.ols
        ypred = ols.predict_error_matrix([self.Xk])[0]
        self.assertAlmostEqual(ypred, self.ypred_k, 3)

    def testPredictYerr_al(self):
        ols = self.ols
        ypred = ols.predict_error_al(self.Xk)[0]
        self.assertAlmostEqual(ypred, self.ypred_k, 3)

    def testPredictYerrSD(self):
        ols = self.ols
        ypred = ols.predict_error(self.Xk, error_calc='SEM')
        ypredm = ols.predict_error_matrix([self.Xk], error_calc='SEM')[0]
        self.assertAlmostEqual(ypred, ypredm, 7)

    def testPredictYerrSD_al(self):
        ols = self.ols
        ypred = ols.predict_error(self.Xk, error_calc='sd')
        ypredal = ols.predict_error_al(self.Xk, error_calc='sd')[0]
        self.assertAlmostEqual(ypred, ypredal, 7)

#    def testCovar(self):
#        ols = self.ols
#        cv = ols.calculate_var_covar()
#        self.assertEqual(cv, cvm)

#    def testCovar(self):
#        ols = self.ols
#        covar = ols.calculate_var_covar()
#        print covar
#        print
#        assert np.array_equal(covar,)

#        print covar
#        print ols._result.cov_params()
#        print ols._result.normalized_cov_params
#    def testPredictYerr2(self):
#        xs = self.xs
#        ys = self.ys
#
#        ols = PolynomialRegressor(xs=xs, ys=ys, fit='parabolic')
#        y = ols.predict_error(5)[0]
# #        yal = ols.predict_error_al(5)[0]
# #        print y, yal
#        self.assertEqual(y, self.Yprederr_5_parabolic)
# #        self.assertEqual(yal, self.Yprederr_5_parabolic)

#============= EOF =============================================
