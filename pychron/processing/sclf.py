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
from scipy.stats import shapiro, skew, norm, ttest_rel
from uncertainties import ufloat

from pychron.core.stats import calculate_mswd, validate_mswd, calculate_weighted_mean
from pychron.pychron_constants import (
    SCHAEN2020_1,
    SCHAEN2020_2,
    SCHAEN2020_3,
    DEINO,
    SCHAEN2020_3youngest,
)


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
            nmean = ufloat(u, e)
            if not mean or nmean < mean:
                mean = nmean
                mean_ans = ais
        # else:
        #     break

    return mean, mean_ans


def schaen_2020_2(ans, **kw):
    """
    weighted mean filter
    :param ans:
    :return: ufloat
    """
    wm, we, ais = 0, 0, []
    for i in range(2, len(ans) - 1):
        ais = ans[:i]
        next_a = ans[i]

        xs, es = age_errors(ais)
        wm, we = calculate_weighted_mean(xs, es)

        rv1 = norm.rvs(loc=wm, scale=we)
        rv2 = norm.rvs(loc=next_a.age, scale=next_a.age_err)
        result = ttest_rel(rv1, rv2)
        if result.pvalue < 0.05:
            return ufloat(wm, we), ais
    else:
        return ufloat(wm, we), ais

        # sed = (le**2+next_a.age_err**2)**0.5
        # t = abs(lwm-next_a.age)/sed

    # for i in range(len(ans) - 2, 1, -1):
    #     lais = ans[:i]
    #     hais = ans[i:]
    #
    #     lxs, les = age_errors(lais)
    #     hxs, hes = age_errors(hais)
    #
    #     lwm, le = calculate_weighted_mean(lxs, les)
    #     hwm, he = calculate_weighted_mean(hxs, hes)
    #     # the two means differ by > 2sigma
    #     if (hwm - he * 2) - (lwm + 2 * le) > 0:
    #         return ufloat(lwm, le), lais


def shapiro_wilk_pvalue(ans):
    xs, es = age_errors(ans)
    if len(xs) >= 3:
        stat, pvalue = shapiro(xs)
        return pvalue


def skewness_value(ans):
    xs, es = age_errors(ans)
    return skew(xs)


def schaen_2020_3youngest(*args, **kw):
    kw["find_youngest"] = True
    return schaen_2020_3(*args, **kw)


def schaen_2020_3(
    ans, alpha=0.05, skew_min=-0.2, skew_max=0.2, find_youngest=False, **kw
):
    """
        normality and goodness-of-fit parameter


        if find_youngest is True find the youngest gaussian population
        if find_youngest is False[default] find the largest gaussian population
    :param threshold:
    :param ans:
    :return: ufloat
    """
    # ans = sorted(ans, key=lambda a: a.age*a.age_err)
    maxn = -1
    mean = ufloat(0, 0)
    mean_ans = []
    # print(alpha, skew_max, skew_min)
    n = len(ans)
    for i in range(0, n + 1):
        if find_youngest:
            if mean_ans:
                break

        for j in range(i + 3, n + 1):
            ais = ans[i:j]
            n = len(ais)

            if not find_youngest:
                if n < maxn:
                    continue

            xs, es = age_errors(ais)
            mswd = calculate_mswd(xs, es)
            valid = validate_mswd(mswd, n)
            # print('mswd ---- ', i, j, mswd, n, maxn, valid)
            if valid:
                stat, pvalue = shapiro(xs)
                # print('shapiro ---- ', pvalue, alpha)
                if pvalue > alpha:
                    skewness = skew(xs)
                    # print('skew ---- ', skewness)
                    if skew_min <= skewness <= skew_max:
                        if find_youngest:
                            m, e = calculate_weighted_mean(xs, es)
                            mm = ufloat(m, e)
                            if not mean or mm < mean:
                                mean = mm
                                mean_ans = ais
                                break
                        else:
                            if maxn < n:
                                maxn = n
                                m, e = calculate_weighted_mean(xs, es)
                                mean = ufloat(m, e)
                                mean_ans = ais

    return mean, mean_ans


OUTLIER_FUNCS = {
    SCHAEN2020_1: schaen_2020_1,
    SCHAEN2020_2: schaen_2020_2,
    SCHAEN2020_3: schaen_2020_3,
    SCHAEN2020_3youngest: schaen_2020_3youngest,
    DEINO: deino_filter,
}


def plot(s, mu, sigma, um3, um2):
    import numpy as np
    import matplotlib.pyplot as plt

    count, bins, ignored = plt.hist(s, 30, density=True)
    plt.plot(
        bins,
        1
        / (sigma * np.sqrt(2 * np.pi))
        * np.exp(-((bins - mu) ** 2) / (2 * sigma**2)),
        linewidth=2,
        color="r",
    )

    plt.vlines(um3.nominal_value, 0, 1)
    plt.vlines(um2.nominal_value, 0, 1, "r")

    plt.show()


if __name__ == "__main__":
    xs = normal(size=400)
    es = normal(size=400) * 3

    class A:
        def __init__(self, x, e):
            self.age = x
            self.age_err = e

    ans = [A(xi, ei) for xi, ei in zip(xs, es)]
    ans = sorted(ans, key=attrgetter("age"))
    print([a.age for a in ans])
    # ans = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    um3 = schaen_2020_3(ans)
    um2 = schaen_2020_2(ans)
    plot(xs, 0, 1, um3, um2)
# ============= EOF =============================================
