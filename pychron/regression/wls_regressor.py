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
from numpy import asarray

try:
    from statsmodels.api import WLS
except ImportError:
    from scikits.statsmodels.api import WLS
#============= local library imports  ==========================
# from pychron.regression.base_regressor import BaseRegressor

from pychron.regression.ols_regressor import OLSRegressor, MultipleLinearRegressor


class WeightedPolynomialRegressor(OLSRegressor):
    def calculate(self):
        if not len(self.xs) or \
                not len(self.ys) or \
                not len(self.yserr):
            return

        if len(self.xs) != len(self.ys) or len(self.xs) != len(self.yserr):
            return

        #xs = self.xs
        #xs = asarray(xs)

        ws = self._get_weights()
        ys = self.ys
        x = self._get_X()
        self._wls = WLS(ys, x,
                        #weights=1 / es
                        weights=ws)
        self._result = self._wls.fit()

    def _get_weights(self):
        es = asarray(self.yserr)
        return es ** -2


class WeightedMultipleLinearRegressor(WeightedPolynomialRegressor, MultipleLinearRegressor):
    pass

#    def calculate_var_covar(self):
#        '''
#            V=[var1        0
#                    var2
#                        .
#                  0         .
#                                varN]
#        '''
#        X = self._get_X()
#        X = matrix(X)
#        V = matrix(diag(self.yserr ** 2))
#        return (X.T * V.I * X).I

#        print self._result.summary()

#    def predict(self, x):
#        x = self._get_X(x)
#        rx = self._result.predict(x)
#        return rx
#    def _calculate_coefficients(self):
#============= EOF =============================================
