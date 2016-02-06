# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Bool
# ============= standard library imports ========================
from numpy import asarray, column_stack, ones_like
# ============= local library imports  ==========================
from statsmodels.regression.linear_model import WLS, OLS
from pychron.core.regression.ols_regressor import MultipleLinearRegressor


class BowlFluxRegressor(MultipleLinearRegressor):
    def _get_X(self, xs=None):
        if xs is None:
            xs = self.xs
        xs = asarray(xs)
        x1, x2 = xs.T
        return column_stack((x1, x2, x1 ** 2, x2 ** 2, x1 * x2, ones_like(x1)))


class PlaneFluxRegressor(MultipleLinearRegressor):
    use_weighted_fit = Bool(False)
    # def calculate_standard_error_fit(self):
    #     e=self.clean_yserr
    #     v=self.clean_ys
    #     w = (e/v)**-2
    #     p = w.sum()**-0.5
    #     print p
    #     return p
    # def _get_degrees_of_freedom(self):
    #     return 6
    # def predict_error(self, x, error_calc=None):
    #     x = asarray(x)
    #     exog=self._get_X(x)
    # # print 'exception', exog
    #     res=self._result
    #     covb = res.cov_params()
    #     # weights=self._get_weights()
    #     weights=res.model.weights
    #     print weights
    #     print covb.shape
    #     print (exog * dot(covb, exog.T).T).sum(1)
    #     predvar=res.mse_resid / weights + (exog * dot(covb, exog.T).T).sum(1)
    #     print predvar**0.5
    #     # print res.mse_resid/weights
    #     return res.mse_resid / weights + (exog * dot(covb, exog.T).T).sum(1)
    #     return wls_prediction_std(self._result, x, weights=self._get_weights())
    #
    #     return 0
    #
    def _get_weights(self):
        e = self.clean_yserr
        if self._check_integrity(e, e):
            return 1 / e ** 2
            return (e / self.clean_ys) ** -2

            #e**0.5 =5.56e-6
            #e**2 = 8900
            #e =10
            #1/e=1e-5
            #1/e**2=2e-8
            #e**-0.5

    def _engine_factory(self, fy, X, check_integrity=True):
        if self.use_weighted_fit:
            return WLS(fy, X, weights=self._get_weights())
        else:
            return OLS(fy, X)

# ============= EOF =============================================
