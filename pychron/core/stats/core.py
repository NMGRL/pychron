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
from numpy import asarray, average, vectorize, corrcoef
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


def chi_squared(x, y, sx, sy, a, b, correlated_errors=True):
    """
        Press et. al 2007 Numerical Recipes
        chi2=Sum((y_i-(a+b*x_i)^2*W_i)
        where W_i=1/(sy_i^2+(b*sx_i)^2)

        a: y intercept
        b: slope

        Mahon 1996 modifies weights for correlated errors

        W_i=1/(sy_i^2+(b*sx_i)^2-k)

        k=2*b*p_i.*sx_i**2

        p: correlation_coefficient

    """
    x = asarray(x)
    y = asarray(y)

    sx = asarray(sx)
    sy = asarray(sy)

    k=0
    if correlated_errors:
        pxy = corrcoef(x, y)[0][1]
        k = 2 * b * pxy * sx ** 2

    w = (sy ** 2 + (b * sx) ** 2 - k) ** -1

    c = ((y - (a + b * x)) ** 2 * w).sum()

    return c


def calculate_mswd2(x, y, ex, ey, a, b, correlated_errors=True):
    """
        see Murray 1994, Press 2007

        calculate chi2
        mswd=chi2/(n-2)
    """
    n = len(x)

    return chi_squared(x, y, ex, ey, a, b, correlated_errors) / (n - 2)

#============= EOF =============================================

