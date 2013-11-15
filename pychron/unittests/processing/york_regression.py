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

#============= standard library imports ========================
import unittest
import numpy as np
#============= local library imports  ==========================
from pychron.regression.new_york_regressor import NewYorkRegressor, ReedYorkRegressor


class NewYorkRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Pearson Data with Weights
        xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
        ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]

        #         xs = [5, 10, 6, 8, 4, 4, 3, 10, 2, 6, 7, 9]
        #         ys = [5, 20, 4, 15, 11, 9, 12, 18, 7, 2, 14, 17]

        wxs = np.array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
        wys = np.array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
        exs = 1 / wxs ** 0.5
        eys = 1 / wys ** 0.5

        cls.reg = NewYorkRegressor(xs=xs, ys=ys, xserr=exs, yserr=eys)

    def setUp(self):
        pass

    def testSlope(self):
        slope = self.reg.get_slope()
        self.assertAlmostEqual(slope, -0.4805, 4)

    def testIntercept(self):
        intercept = self.reg.get_intercept()
        self.assertAlmostEqual(intercept, 5.4799, 4)

    def testSlopeError(self):
        err = self.reg.get_slope_error()
        self.assertAlmostEqual(err, 0.0702, 4)

# #
#     def testPredict(self):
#         y = self.reg.predict(0)
#         self.assertAlmostEqual(y, 5.4799, 4)

#     def testPearsons_r(self):
#         r = self.reg.calculate_pearsons_r()
#         self.assertAlmostEqual(0.6668, r, places=4)
#     def testSlopeError(self):
#         se = self.reg.get_slope_error()
#         self.assertAlmostEqual(se, 0.0702, 4)

class YorkRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xs = [0.03692, 1.07118]
        exs = [0.00061, 0.00066]
        ys = [0.003121, 0.00022]
        eys = [0.0003, 0.000013]

        xs = [0.89, 1.0, 0.92, 0.87, 0.9, 0.86, 1.08, 0.86, 1.25,
              1.01, 0.86, 0.85, 0.88, 0.84, 0.79, 0.88, 0.70, 0.81,
              0.88, 0.92, 0.92, 1.01, 0.88, 0.92, 0.96, 0.85, 1.04
        ]
        ys = [0.67, 0.64, 0.76, 0.61, 0.74, 0.61, 0.77, 0.61, 0.99,
              0.77, 0.73, 0.64, 0.62, 0.63, 0.57, 0.66, 0.53, 0.46,
              0.79, 0.77, 0.7, 0.88, 0.62, 0.80, 0.74, 0.64, 0.93
        ]
        exs = np.ones(27) * 0.01
        eys = np.ones(27) * 0.01

        #         xs = [  1.333, -1.009, 9.720, -2.079, 8.920, -0.938, 10.94, 5.138, 11.37, 9.421]
        #         exs = [ 2.469 , 6.363, 6.045 , 4.061, 5.325, 5.865 , 3.993, 3.787, 3.693, 4.687]
        #         ys = [ -1.367 , 7.232, -0.593, 7.124, 0.468, 8.664 , 5.854, 13.35, 4.279, 11.63]
        #         eys = [0.297  , 4.672 , 2.014, 0.022, 6.868, 2.834 , 4.647, 4.728, 2.274, 4.659]


        # Pearson Data with Weights
        xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
        ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
        wxs = np.array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
        wys = np.array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
        exs = 1 / wxs ** 0.5
        eys = 1 / wys ** 0.5

        # reed 1992 solutions
        cls.pred_slope = -0.4805
        cls.pred_intercept = 5.4799
        cls.pred_intercept_error = 0.3555
        cls.pred_slope_error = 0.0702

        cls.reg = ReedYorkRegressor(
            ys=ys,
            xs=xs,
            xserr=exs,
            yserr=eys
        )


    def testSlope(self):
        slope = self.reg.get_slope()
        self.assertAlmostEqual(self.pred_slope, slope, places=3)

    def testIntercept(self):
        intercept = self.reg.get_intercept()
        self.assertAlmostEqual(self.pred_intercept, intercept, places=3)


#============= EOF =============================================
