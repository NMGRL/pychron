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
# from traits.api import HasTraits
# from pychron.core.ui import set_toolkit
# set_toolkit('qt4')
# ============= standard library imports ========================
from unittest import TestCase

from numpy import linspace, polyval

# ============= local library imports  ==========================
from pychron.core.regression.mean_regressor import MeanRegressor  #, WeightedMeanRegressor
from pychron.core.regression.new_york_regressor import ReedYorkRegressor, NewYorkRegressor
from pychron.core.regression.ols_regressor import OLSRegressor
# from pychron.core.regression.york_regressor import YorkRegressor
from pychron.core.regression.tests.standard_data import mean_data, filter_data, ols_data, pearson

# class RegressionTestCase(TestCase):
#     def setUp(self):
#         self.reg = MeanRegressor()
#
#     def test_something(self):
#         self.assertEqual(True, False)

class RegressionTestCase(object):
    @classmethod
    def setUpClass(cls):
        cls.reg = cls.reg_klass()

    def testN(self):
        self.assertEqual(self.reg.n, self.solution['n'])


class MeanRegressionTest(RegressionTestCase, TestCase):
    reg_klass = MeanRegressor

    def setUp(self):
        n = 1e5
        xs, ys, sol = mean_data(n=n)
        self.reg.trait_set(xs=xs, ys=ys)
        self.solution = sol

    def testMean(self):
        self.assertAlmostEqual(self.reg.mean, self.solution['mean'], 2)

    def testStd(self):
        self.assertAlmostEqual(self.reg.std, self.solution['std'], 2)


class OLSRegressionTest(RegressionTestCase, TestCase):
    reg_klass = OLSRegressor

    def setUp(self):
        xs, ys, sol = ols_data()
        self.reg.trait_set(xs=xs, ys=ys, fit='linear')
        self.solution = sol
        self.reg.calculate()

    def testSlope(self):
        cs = self.reg.coefficients
        self.assertAlmostEqual(cs[-1], self.solution['slope'], 4)

    def testYIntercept(self):
        cs = self.reg.coefficients
        self.assertAlmostEqual(cs[0], self.solution['y_intercept'], 4)

    def testPredictErrorSEM(self):
        e = self.reg.predict_error(self.solution['pred_x'], error_calc='SEM')
        self.assertAlmostEqual(e, self.solution['pred_error'], 3)


class OLSRegressionTest2(RegressionTestCase, TestCase):
    reg_klass = OLSRegressor
    def setUp(self):
        n=100
        coeffs=[2.12,1.13,5.14]
        xs = linspace(0, 100, n)
        ys = polyval(coeffs, xs)

        self.reg.trait_set(xs=xs, ys=ys, fit='parabolic')

        sol = {'coefficients':coeffs, 'n':n}
        self.solution = sol
        self.reg.calculate()

    def testcoefficients(self):
        self.assertListEqual(list(map(lambda x: round(x, 6),
                                      self.reg.coefficients[::-1])),
                             self.solution['coefficients'])

class FilterOLSRegressionTest(RegressionTestCase, TestCase):
    reg_klass = OLSRegressor

    def setUp(self):
        xs, ys, sol = filter_data()
        self.reg.trait_set(xs=xs, ys=ys, fit='linear',
                           filter_outliers_dict={'filter_outliers': True, 'iterations': 1, 'std_devs': 2})
        self.solution = sol
        self.reg.calculate()

    def testSlope(self):
        cs = self.reg.coefficients
        self.assertAlmostEqual(cs[-1], self.solution['slope'], 4)

    def testYIntercept(self):
        cs = self.reg.coefficients
        self.assertAlmostEqual(cs[0], self.solution['y_intercept'], 4)

    def testPredictErrorSEM(self):
        e = self.reg.predict_error(self.solution['pred_x'], error_calc='SEM')
        # e=self.reg.coefficient_errors[0]
        self.assertAlmostEqual(e, self.solution['pred_error'], 3)


class PearsonRegressionTest(RegressionTestCase):
    kind = ''
    def setUp(self):
        xs, ys, wxs, wys = pearson()

        exs = wxs ** -0.5
        eys = wys ** -0.5

        self.reg.trait_set(xs=xs, ys=ys,
                                     xserr=exs,
                                     yserr=eys)
        self.reg.calculate()
        self.solution={'n':len(xs)}

    def test_slope(self):
        exp = pearson(self.kind)
        self.assertAlmostEqual(self.reg.slope, exp['slope'], 4)

    def test_y_intercept(self):
        expected = pearson(self.kind)
        self.assertAlmostEqual(self.reg.intercept, expected['intercept'], 4)

    def test_mswd(self):
        expected = pearson(self.kind)
        self.assertAlmostEqual(self.reg.mswd, expected['mswd'], 3)


class ReedRegressionTest(PearsonRegressionTest, TestCase):
    reg_klass = ReedYorkRegressor
    kind = 'reed'


class NewYorkRegressionTest(PearsonRegressionTest, TestCase):
    reg_klass = NewYorkRegressor
    kind = 'reed'
# class WeightedMeanRegressionTest(RegressionTestCase, TestCase):
#     @staticmethod
#     def regressor_factory():
#         return WeightedMeanRegressor()
#
#     def setUp(self):
#         xs, ys, yes, sol = weighted_mean_data()
#         self.reg.trait_set(xs=xs, ys=ys,
#                            yserr=yes,
#         )
#         self.solution = sol
#         self.reg.calculate()
#
#     def testMean(self):
#         v = self.reg.mean
#         self.assertEqual(v, self.solution['mean'])


# class WeightedMeanRegressionTest(TestCase):
#     def setUp(self):
#         n = 1000
#         ys = np.ones(n) * 5
#         #        es = np.random.rand(n)
#         es = np.ones(n)
#         ys = np.hstack((ys, [5.1]))
#         es = np.hstack((es, [1000]))
# #        print 'exception', es
#         self.reg = WeightedMeanRegressor(ys=ys, errors=es)

#    def testMean(self):
#        m = self.reg.mean
#        self.assertEqual(m, 5)

# class RegressionTest(TestCase):
#     def setUp(self):
#         self.x = np.array([1, 2, 3, 4, 4, 5, 5, 6, 6, 7])
#         self.y = np.array([7, 8, 9, 8, 9, 11, 10, 13, 14, 13])
#
#     def testMeans(self):
#         xm = self.x.mean()
#         ym = self.y.mean()
#         self.assertEqual(xm, 4.3)
#         self.assertEqual(ym, 10.2)
#
#
# class CITest(TestCase):
#     def setUp(self):
#         self.x = np.array([0, 12, 29.5, 43, 53, 62.5, 75.5, 85, 93])
#         self.y = np.array([8.98, 8.14, 6.67, 6.08, 5.9, 5.83, 4.68, 4.2, 3.72])
#
#     def testUpper(self):
#         reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
#         l, u = reg.calculate_ci([0, 10, 100])
#         for ui, ti in zip(u, [9.16, 8.56, 3.83]):
#             self.assertAlmostEqual(ui, ti, delta=0.01)
#
#     def testLower(self):
#         reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
#         l, u = reg.calculate_ci([0])
#
#         self.assertAlmostEqual(l[0], 8.25, delta=0.01)
#
#     def testSYX(self):
#         reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
#         self.assertAlmostEqual(reg.get_syx(), 0.297, delta=0.01)
#
#     def testSSX(self):
#         reg = PolynomialRegressor(xs=self.x, ys=self.y, degree=1)
#         self.assertAlmostEqual(reg.get_ssx(), 8301.389, delta=0.01)


# class WLSRegressionTest(TestCase):
#     def setUp(self):
#         self.xs = np.linspace(0, 10, 10)
#         self.ys = np.random.normal(self.xs, 1)
#
#         '''
#             draper and smith p.8
#         '''
#         self.xs = [35.3, 29.7, 30.8, 58.8, 61.4, 71.3, 74.4, 76.7, 70.7, 57.5,
#                    46.4, 28.9, 28.1, 39.1, 46.8, 48.5, 59.3, 70, 70, 74.5, 72.1,
#                    58.1, 44.6, 33.4, 28.6
#         ]
#         self.ys = [10.98, 11.13, 12.51, 8.4, 9.27, 8.73, 6.36, 8.50,
#                    7.82, 9.14, 8.24, 12.19, 11.88, 9.57, 10.94, 9.58,
#                    10.09, 8.11, 6.83, 8.88, 7.68, 8.47, 8.86, 10.36, 11.08
#         ]
#         self.es = np.random.normal(1, 0.5, len(self.xs))
#
#         self.slope = -0.0798
#         self.intercept = 13.623
#         self.Xk = 28.6
#         self.ypred_k = 0.3091
#         xs = self.xs
#         ys = self.ys
#         es = self.es
#         self.wls = WeightedPolynomialRegressor(xs=xs, ys=ys,
#                                                yserr=es, fit='linear')
#
#     def testVarCovar(self):
#         wls = self.wls
#         cv = wls.var_covar
#         print cv
#         print wls._result.normalized_cov_params
#
#     #        print wls._result.cov_params()


# class OLSRegressionTest(TestCase):
#     def setUp(self):
#         self.xs = np.linspace(0, 10, 10)
#         #        self.ys = np.random.normal(self.xs, 1)
#         #        print self.ys
#         self.ys = [-1.8593967, 3.15506254, 1.82144207, 4.58729807, 4.95813564,
#                    5.71229382, 7.04611731, 8.14459843, 10.27429285, 10.10989719]
#
#         '''
#             draper and smith p.8
#         '''
#         self.xs = [35.3, 29.7, 30.8, 58.8, 61.4, 71.3, 74.4, 76.7, 70.7, 57.5,
#                    46.4, 28.9, 28.1, 39.1, 46.8, 48.5, 59.3, 70, 70, 74.5, 72.1,
#                    58.1, 44.6, 33.4, 28.6
#         ]
#         self.ys = [10.98, 11.13, 12.51, 8.4, 9.27, 8.73, 6.36, 8.50,
#                    7.82, 9.14, 8.24, 12.19, 11.88, 9.57, 10.94, 9.58,
#                    10.09, 8.11, 6.83, 8.88, 7.68, 8.47, 8.86, 10.36, 11.08
#         ]
#
#         self.slope = -0.0798
#         self.intercept = 13.623
#         self.Xk = 28.6
#         self.ypred_k = 0.3091
#         xs = self.xs
#         ys = self.ys
#         ols = PolynomialRegressor(xs=xs, ys=ys, fit='linear')
#
#         self.ols = ols
#
#     def testSlope(self):
#         ols = self.ols
#         b, s = ols.coefficients
#         self.assertAlmostEqual(s, self.slope, 4)
#
#     def testIntercept(self):
#         ols = self.ols
#         b, s = ols.coefficients
#         self.assertAlmostEqual(b, self.intercept, 4)
#         self.assertAlmostEqual(ols.predict(0), self.intercept, 4)
#
#     def testPredictYerr(self):
#         ols = self.ols
#         ypred = ols.predict_error(self.Xk, error_calc='SEM')
#         self.assertAlmostEqual(ypred, self.ypred_k, 3)
#
#     def testPredictYerr_matrix(self):
#         ols = self.ols
#         ypred = ols.predict_error_matrix([self.Xk])[0]
#         self.assertAlmostEqual(ypred, self.ypred_k, 3)
#
#     def testPredictYerr_al(self):
#         ols = self.ols
#         ypred = ols.predict_error_al(self.Xk)[0]
#         self.assertAlmostEqual(ypred, self.ypred_k, 3)
#
#     def testPredictYerrSD(self):
#         ols = self.ols
#         ypred = ols.predict_error(self.Xk, error_calc='SEM')
#         ypredm = ols.predict_error_matrix([self.Xk], error_calc='SEM')[0]
#         self.assertAlmostEqual(ypred, ypredm, 7)
#
#     def testPredictYerrSD_al(self):
#         ols = self.ols
#         ypred = ols.predict_error(self.Xk, error_calc='sd')
#         ypredal = ols.predict_error_al(self.Xk, error_calc='sd')[0]
#         self.assertAlmostEqual(ypred, ypredal, 7)

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

# ============= EOF =============================================
