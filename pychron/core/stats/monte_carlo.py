# ===============================================================================
# Copyright 2014 Jake Ross
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
# ============= standard library imports ========================

from numpy import zeros, percentile, array, random, abs as nabs, column_stack
from scipy.stats import norm


# ============= local library imports  ==========================

class MonteCarloEstimator(object):

    def __init__(self, ntrials, regressor, seed=None):
        self.regressor = regressor
        self.ntrials = ntrials
        self.seed = seed

    def _calculate(self, nominal_ys, ps):
        res = nominal_ys - ps
        pct = (15.87, 84.13)

        a, b = array([percentile(ri, pct) for ri in res.T]).T
        a, b = nabs(a), nabs(b)
        return (a + b) * 0.5

    def _get_dist(self, n, npts):
        if self.seed:
            random.seed(self.seed)

        ndist = norm()
        ntrials = self.ntrials

        ga = ndist.rvs((ntrials, n))
        ps = zeros((ntrials, npts))
        return ndist, ga, ps

    def _estimate(self, pts, pexog, ys=None, yserr=None):
        reg = self.regressor
        nominal_ys = reg.predict(pts)

        if ys is None:
            ys = reg.ys
        if yserr is None:
            yserr = reg.yserr

        n, npts = len(ys), len(pts)

        ntrials = self.ntrials
        ndist, ga, ps = self._get_dist(n, npts)
        pred = reg.fast_predict2
        yp = ys + yserr * ga

        if hasattr(pexog, '__call__'):
            for i in range(ntrials):
                ps[i] = pred(yp[i], pexog(i))
        else:
            for i in range(ntrials):
                ps[i] = pred(yp[i], pexog)

        return nominal_ys, self._calculate(nominal_ys, ps)


class RegressionEstimator(MonteCarloEstimator):
    def estimate(self, pts):
        reg = self.regressor
        pexog = reg.get_exog(pts)

        return self._estimate(pts, pexog, ys=reg.clean_ys, yserr=reg.clean_yserr)


class FluxEstimator(MonteCarloEstimator):
    def estimate_position_err(self, pts, error):
        reg = self.regressor
        ox, oy = pts.T

        n, npts = len(reg.ys), len(pts)

        ntrials = self.ntrials
        ndist, ga, ps = self._get_dist(n, npts)

        pgax = ndist.rvs((ntrials, npts))
        pgay = ndist.rvs((ntrials, npts))

        pgax *= error
        pgay *= error

        def get_pexog(i):
            return reg.get_exog(column_stack((ox + pgax[i], oy + pgay[i])))

        return self._estimate(pts, get_pexog, yserr=0)

    def estimate(self, pts):

        reg = self.regressor
        pexog = reg.get_exog(pts)

        return self._estimate(pts, pexog)

# ============= EOF =============================================
