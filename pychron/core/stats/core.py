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
from numpy import asarray, average, vectorize
from scipy.stats import chi2
#============= local library imports  ==========================
def _kronecker(ii, jj):
    return int(ii == jj)


kronecker = vectorize(_kronecker)


def calculate_mswd(x, errs, k=1):
    mswd_w = 0
    n = len(x)
    if n >= 2:
        x = asarray(x)
        errs = asarray(errs)
        xmean_w, _err = calculate_weighted_mean(x, errs)

        ssw = (x - xmean_w) ** 2 / errs ** 2
        mswd_w = ssw.sum() / float(n - k)

    #         xmean_u = x.mean()
    #         ssu = (x - xmean_u) ** 2 / errs ** 2
    #         mswd_u = ssu.sum() / float(n - k)
    #         print mswd_w, mswd_u

    return mswd_w


def calculate_weighted_mean(x, errs, error=0):
    x = asarray(x)
    errs = asarray(errs)
    weights = 1 / errs ** 2
    #     weights = asarray(map(lambda e: 1 / e ** 2, errs))

    #     wtot = weights.sum()
    #     wmean = (weights * x).sum() / wtot

    wmean, sum_weights = average(x, weights=weights, returned=True)
    if error == 0:
        werr = sum_weights ** -0.5
    elif error == 1:
        werr = 1
    return wmean, werr


def validate_mswd(mswd, n, k=1):
    '''
         is mswd acceptable based on Mahon 1996
         
         does the mswd fall in the %95 confidence interval of the reduced chi2
         reduced chi2 =chi2/dof
         
         http://en.wikipedia.org/wiki/Goodness_of_fit
         http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html#scipy.stats.chi2
    '''
    if n < 2:
        return

    dof = n - k
    # calculate the reduced chi2 95% interval for given dof
    # use scale parameter to calculate the chi2_reduced from chi2

    rv = chi2(dof, scale=1 / float(dof))
    low, high = rv.interval(0.95)
    return bool(low <= mswd <= high)


def chi_squared(x, y, sx, sy, a, b):
    """
        Press et. al 2007 Numerical Recipes
        chi2=Sum((y_i-(a+b*x_i)^2*W_i)
        where W_i=1/(sy_i^2+(b*sx_i)^2)

        a: y intercept
        b: slope

    """
    x = asarray(x)
    y = asarray(y)

    sx = asarray(sx)
    sy = asarray(sy)

    w = (sy ** 2 + (b * sx) ** 2) ** -1

    c = ((y - (a + b * x)) ** 2 * w).sum()

    return c


def calculate_mswd2(x, y, ex, ey, a, b):
    """
        see Murray 1994, Press 2007

        calculate chi2
        mswd=chi2/(n-2)
    """
    n = len(x)
    return chi_squared(x, y, ex, ey, a, b) / (n - 2)

#============= EOF =============================================
#    if 1 <= dof <= 25:
#        table = {
#           1:(0.001, 5.020),
#           2:(0.025, 3.690),
#           3:(0.072, 3.117),
#           4:(0.121, 2.775),
#           5:(0.166, 2.560),
#           6:(0.207, 2.400),
#           7:(0.241, 2.286),
#           8:(0.273, 2.188),
#           9:(0.300, 2.111),
#           10:(0.325, 2.050),
#           11:(0.347, 1.991),
#           12:(0.367, 1.942),
#           13:(0.385, 1.900),
#           14:(0.402, 1.864),
#           15:(0.417, 1.833),
#           16:(0.432, 1.800),
#           17:(0.445, 1.776),
#           18:(0.457, 1.750),
#           19:(0.469, 1.732),
#           20:(0.480, 1.710),
#           21:(0.490, 1.690),
#           22:(0.500, 1.673),
#           23:(0.509, 1.657),
#           24:(0.517, 1.642),
#           25:(0.524, 1.624),
#           }
#        low, high = table[n]
#    else:
#        low, high = (0.524, 1.624)
