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


class RegressionEstimator(MonteCarloEstimator):
    def estimate(self, pts):
        reg = self.regressor
        pexog = reg.get_exog(pts)
        nominal_ys = reg.predict(pts)

        ys = reg.clean_ys
        yserr = reg.clean_yserr

        ndist, ga, ps = self._get_dist(len(ys), len(pts))
        pred = reg.fast_predict2
        yp = ys+yserr*ga
        for i in range(self.ntrials):

            ps[i] = pred(yp[i], pexog)

        return nominal_ys, self._calculate(nominal_ys, ps)


class FluxEstimator(MonteCarloEstimator):
    def __init__(self, ntrials, regressor, position_only, position_error, mean_position_only=False, mean_position_error=0):
        super(FluxEstimator, self).__init__(ntrials, regressor)

        self.position_error = position_error
        self.position_only = position_only
        self.mean_position_error = mean_position_error
        self.mean_position_only = mean_position_only

    def estimate(self, pts):
        reg = self.regressor
        pexog = reg.get_exog(pts)
        nominal_ys = reg.predict(pts)
        ys = reg.ys
        yserr = reg.yserr

        n, npts = len(ys), len(pts)

        ntrials = self.ntrials
        ndist, ga, ps = self._get_dist(n, npts)

        pred = reg.fast_predict2
        if self.mean_position_only or self.position_only:
            yserr = 0

        yp = ys + yserr * ga
        if self.mean_position_error:
            pgax = ndist.rvs((ntrials, n))
            pgay = ndist.rvs((ntrials, n))

            xs = reg.clean_xs

            ox, oy = xs.T
            for i in range(ntrials):
                x = ox + self.mean_position_error * pgax[i]
                y = oy + self.mean_position_error * pgay[i]
                x = reg.get_exog(column_stack((x, y)))
                ps[i] = pred(yp[i], pexog, exog=x)
        elif self.position_error:
            pgax = ndist.rvs((ntrials, n))
            pgay = ndist.rvs((ntrials, n))

            ox, oy = pts.T
            for i in range(ntrials):
                x = ox + self.position_error * pgax[i]
                y = oy + self.position_error * pgay[i]
                pexog = reg.get_exog(column_stack((x, y)))
                ps[i] = pred(yp[i], pexog)

        else:
            for i in range(ntrials):
                ps[i] = pred(yp[i], pexog)

        return nominal_ys, self._calculate(nominal_ys, ps)


def monte_carlo_error_estimation(reg, nominal_ys, pts, ntrials=100, position_error=None,
                                 position_only=False,
                                 mean_position_error=None,
                                 mean_position_only=False, seed=None):
    pexog = reg.get_exog(pts)
    ys = reg.ys
    yserr = reg.yserr

    n = len(ys)
    npts = len(pts)
    if seed:
        random.seed(seed)
    ndist = norm()
    ga = ndist.rvs((ntrials, n))
    ps = zeros((ntrials, npts))

    pred = reg.fast_predict2
    if mean_position_only or position_only:
        yserr = 0

    yp = ys + yserr * ga
    if mean_position_error:
        pgax = ndist.rvs((ntrials, n))
        pgay = ndist.rvs((ntrials, n))

        xs = reg.clean_xs

        ox, oy = xs.T
        for i in range(ntrials):
            x = ox + mean_position_error * pgax[i]
            y = oy + mean_position_error * pgay[i]
            x = reg.get_exog(column_stack((x, y)))
            ps[i] = pred(yp[i], pexog, exog=x)
    elif position_error:
        pgax = ndist.rvs((ntrials, n))
        pgay = ndist.rvs((ntrials, n))

        # xs = reg.clean_xs
        ox, oy = pts.T
        for i in range(ntrials):
            x = ox + position_error * pgax[i]
            y = oy + position_error * pgay[i]
            pexog = reg.get_exog(column_stack((x, y)))
            ps[i] = pred(yp[i], pexog)

    else:
        for i in range(ntrials):
            ps[i] = pred(yp[i], pexog)

    res = nominal_ys - ps

    res = res.T

    pct = (15.87, 84.13)

    a, b = array([percentile(ri, pct) for ri in res]).T
    a, b = nabs(a), nabs(b)
    return (a + b) * 0.5

# def perturb(pred, exog, nominal_ys, y_es, ga, yp):
# def perturb(pred, exog, nominal_ys, ys, es, ga):
# for i, (y, e) in enumerate(y_es):
#     yp[i] = y + (e * ga[i])
# yp = ys + es * ga
# pys = pred(yp, exog)
# return nominal_ys - pys


# if __name__ == '__main__':
#     from pychron.core.regression.flux_regressor import PlaneFluxRegressor
#     from pychron.core.codetools.simple_timeit import timethis
#     import csv
#
#     random.seed(123456789)
#
#     x = []
#     y = []
#     j = []
#     je = []
#     p = '/Users/ross/Sandbox/monte_carlo.txt'
#     with open(p, 'r') as rfile:
#         reader = csv.reader(fp)
#         for l in reader:
#             if not l[0][0] == '#':
#                 a, b, c, d = map(float, l)
#                 x.append(a)
#                 y.append(b)
#                 j.append(c)
#                 je.append(d)
#                 # break
#
#     x = array(x)
#     y = array(y)
#     xy = vstack((x, y)).T
#
#     j = array(j)
#
#     for ni in (10, 100, 1000, 10000, 20000):
#         # for n in (10, 20, 100, 1000):
#         r = PlaneFluxRegressor(xs=xy, ys=j, yserr=je, error_calc_type='SD')
#         r.calculate(filtering=True)
#         errors = timethis(monte_carlo_error_estimation, args=(r, r.predict(xy), xy),
#                           kwargs=dict(ntrials=ni))
#         print ni, errors
#
# '''
# timethis $$$$$$$$$$$$$$$$$$$$ 0.00164294242859s
# timethis $$$$$$$$$$$$$$$$$$$$ 0.0126359462738s
# timethis $$$$$$$$$$$$$$$$$$$$ 0.119521141052s
# timethis $$$$$$$$$$$$$$$$$$$$ 1.32541584969s
# '''
# ============= EOF =============================================
