# ===============================================================================
# Copyright 2021 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from operator import attrgetter
from numpy import array, argmax, delete
from numpy.random import normal
from scipy.stats import shapiro, skew, norm
from uncertainties import ufloat

from pychron.core.stats import calculate_mswd, validate_mswd, calculate_weighted_mean


def age_errors(ais):
    xs = [ai.age for ai in ais]
    es = [ai.age_err for ai in ais]

    return array(xs), array(es)


def deino_filter(ans, **kw):
    """
    remove most extreme value

    ie. inverse variance weighted deviation from mean
    :param ans:
    :return:
    """
    ans = array(ans)
    for i in range(len(ans)):
        if len(ans) < 3:
            break

        xs, es = age_errors(ans)

        mswd = calculate_mswd(xs, es)
        if validate_mswd(mswd, len(ans)):
            break

        mu = xs.mean()
        wd = ((mu - xs) / es) ** 2

        idx = argmax(wd)
        ans = delete(ans, idx)

    return None, ans


def schaen_2020_1(ans, **kw):
    """
    low mswd weighted mean
    :param ans:
    :return: ufloat, idxs of excluded analyses
    """
    mean = ufloat(0, 0)
    mean_ans = []
    for i in range(2, len(ans)):
        ais = ans[:i]
        xs, es = age_errors(ais)
        mswd = calculate_mswd(xs, es)
        valid = validate_mswd(mswd, len(xs))
        if valid:
            u, e = calculate_weighted_mean(xs, es)
            mean = ufloat(u, e)
            mean_ans = ais
        else:
            break

    return mean, mean_ans


def schaen_2020_2(ans, **kw):
    """
    weighted mean filter
    :param ans:
    :return: ufloat
    """

    for i in range(len(ans) - 2, 1, -1):
        lais = ans[:i]
        hais = ans[i:]

        lxs, les = age_errors(lais)
        hxs, hes = age_errors(hais)

        lwm, le = calculate_weighted_mean(lxs, les)
        hwm, he = calculate_weighted_mean(hxs, hes)
        # the two means differ by > 2sigma
        if (hwm - he * 2) - (lwm + 2 * le) > 0:
            return ufloat(lwm, le), lais


def schaen_2020_3(ans, alpha=0.05, skew_min=-0.2, skew_max=0.2, **kw):
    """
        normality and goodness-of-fit parameter
    :param threshold:
    :param ans:
    :return: ufloat
    """
    # ans = sorted(ans, key=lambda a: a.age*a.age_err)
    maxn = -1
    mean = ufloat(0, 0)
    mean_ans = []
    print(alpha, skew_max, skew_min)
    for i in range(0, len(ans) + 1):
        for j in range(i + 3, len(ans) + 1):
            ais = ans[i:j]
            n = len(ais)
            if n < maxn:
                continue

            xs, es = age_errors(ais)
            mswd = calculate_mswd(xs, es)
            valid = validate_mswd(mswd, n)
            print(i, j, mswd, n, maxn, valid)
            if valid:
                stat, pvalue = shapiro(xs)
                print(pvalue, alpha)
                if pvalue > alpha:
                    skewness = skew(xs)
                    if skew_min <= skewness <= skew_max:
                        if maxn < n:
                            maxn = n
                            m, e = calculate_weighted_mean(xs, es)
                            mean = ufloat(m, e)
                            mean_ans = ais

    return mean, mean_ans


def plot(s, mu, sigma, um3, um2):
    import numpy as np
    import matplotlib.pyplot as plt
    count, bins, ignored = plt.hist(s, 30, density=True)
    plt.plot(bins, 1 / (sigma * np.sqrt(2 * np.pi)) *
             np.exp(- (bins - mu) ** 2 / (2 * sigma ** 2)),
             linewidth=2, color='r')

    plt.vlines(um3.nominal_value, 0, 1)
    plt.vlines(um2.nominal_value, 0, 1, 'r')

    plt.show()


if __name__ == '__main__':
    xs = normal(size=400)
    es = normal(size=400) * 3


    class A:
        def __init__(self, x, e):
            self.age = x
            self.age_err = e


    ans = [A(xi, ei) for xi, ei in zip(xs, es)]
    ans = sorted(ans, key=attrgetter('age'))
    print([a.age for a in ans])
    # ans = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    um3 = schaen_2020_3(ans)
    um2 = schaen_2020_2(ans)
    plot(xs, 0, 1, um3, um2)
# ============= EOF =============================================
