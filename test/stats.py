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
from numpy import array
#============= local library imports  ==========================
from unittest import TestCase

from pychron.core.regression.regressors.polynomial import PolynomialRegressor
class StatsTests(TestCase):
    def setUp(self):
#        self.m = 10
#        self.b = -90
#        self.berr = 0

#        self.xs = xs = linspace(0, 100)
#        self.ys = ys = xs * xs + 2

#        self.ys = ys = self.m * xs + self.b
        xs = [1.34817935e09, 1.34818086e09, 1.34818107e09, 1.34818129e09, 1.34818150e09, 1.34818171e09]

        xs = array(xs)
        xs = xs - xs[-1]
        ys = [ 12.69424305, 15.67507165, 15.9631792, 16.28923218, 16.60528924, 16.86075035]
        self.regressor = PolynomialRegressor(xs=xs, ys=ys, degree=1)
        self.regressor.calculate()
        print self.regressor.coefficients

    def testLinearIntercept(self):
        print self.regressor.coefficients
#        b = self.regressor.calculate_y(0)
#        self.assertAlmostEqual(b, self.b, places=10)
#
#    def testLinearError(self):
#        berr = self.regressor.calculate_yerr(0)
#        self.assertAlmostEqual(berr, self.berr, places=10)
#
#    def testCI(self):
#        cil, ciu = self.regressor.calculate_ci(0)
#        self.assertAlmostEqual(abs(cil[0] - ciu[0]), 0 , places=10)

#============= EOF =============================================
