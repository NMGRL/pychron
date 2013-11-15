#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
from numpy import asarray, column_stack, ones_like
#============= local library imports  ==========================
from pychron.regression.wls_regressor import WeightedMultipleLinearRegressor
#class FluxRegressor(MultipleLinearRegressor):
class BowlFluxRegressor(WeightedMultipleLinearRegressor):
    def _get_X(self, xs=None):
        if xs is None:
            xs = self.xs
        xs = asarray(xs)
        x1, x2 = xs.T
        return column_stack((x1, x2, x1 ** 2, x2 ** 2, x1 * x2, ones_like(x1)))


class PlaneFluxRegressor(WeightedMultipleLinearRegressor):
    pass

#============= EOF =============================================
