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
from numpy import zeros, percentile, array
from scipy.stats import norm
# ============= local library imports  ==========================


def monte_carlo_error_estimation(reg, nominal_ys, pts, ntrials=100):
    exog = reg.get_exog(pts)
    ys = reg.ys
    yserr = reg.yserr
    n = len(ys)
    yes = array((ys, yserr)).T
    ga = norm().rvs((ntrials, n))
    yp = zeros(n)
    res = zeros((ntrials, len(pts)))

    pred = reg.fast_predict2
    for i in xrange(ntrials):
        res[i] = perturb(pred, exog, nominal_ys, yes, ga[i], yp)

    res = res.T
    ret = zeros(len(pts))
    pct = (15.87, 84.13)
    for i, po in enumerate(pts):
        ri = res[i]
        ai, bi = percentile(ri, pct)
        ret[i] = (abs(ai) + abs(bi)) * 0.5

    return ret


def perturb(pred, exog, nominal_ys, y_es, ga, yp):
    for i, (y, e) in enumerate(y_es):
        yp[i] = y + e * ga[i]

    pys = pred(yp, exog)
    return nominal_ys - pys


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
