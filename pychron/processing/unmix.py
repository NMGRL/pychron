# ===============================================================================
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
# ===============================================================================

import matplotlib.pyplot as plt

# ============= enthought library imports =======================
# from __future__ import absolute_import
# from __future__ import print_function
# import csv
#
# import numpy as np
# from six.moves import range
# from six.moves import zip
# ============= standard library imports ========================
# ============= local library imports  ==========================
from numpy import exp, pi, sqrt, hstack, arange

#
# def unmix(ages, errors, initial_guess):
#     ages_errors = list(zip(ages, errors))
#
#     ts = initial_guess[0]
#     pis = initial_guess[1]
#
#     niterations = 20
#     for _ in range(niterations):
#         tis_n = []
#         pis_n = []
#         for pi, tj in zip(pis, ts):
#             pn, tn = _unmix(ages_errors, pi, tj, pis, ts)
#             tis_n.append(tn)
#             pis_n.append(pn)
#         pis = pis_n
#         ts = tis_n
#     #        print ts, pis
#     return ts, pis
#
#
# def _unmix(ages_errors, pi_j, tj_o, pis, ts):
#     n = len(ages_errors)
#     s = sum([pi_j * fij(ai_ei, tj_o) / Si(pis, ai_ei, ts)
#              for ai_ei in ages_errors])
#
#     pi_j = 1 / float(n) * s
#
#     a = sum([pi_j * ai_ei[0] * fij(ai_ei, tj_o) / (ai_ei[1] ** 2 * Si(pis, ai_ei, ts))
#              for ai_ei in ages_errors])
#     b = sum([pi_j * fij(ai_ei, tj_o) / (ai_ei[1] ** 2 * Si(pis, ai_ei, ts))
#              for ai_ei in ages_errors])
#     tj = a / b
#     return pi_j, tj
#
#
# def fij(ai_ei, tj):
#     ai, ei = ai_ei
#     return 1 / (ei * (2 * np.pi) ** 0.5) * np.exp(-(ai - tj) ** 2 / (2 * ei ** 2))
#
#
# def Si(pis, ai_ei, ts):
#     return sum([pik * fij(ai_ei, tk) for pik, tk in zip(pis, ts)])
from numpy.random.mtrand import normal


def unmix(ages, ps, ts):
    """
    ages = list of 2-tuples (age, 1sigma )

    :param ages:
    :param ps:
    :param ts:
    :return:
    """
    niterations = 20
    for _ in range(niterations):
        tis_n = []
        pis_n = []
        for pi, ti in zip(ps, ts):
            pn, tn = tj(ages, pi, ti, ps, ts)
            tis_n.append(tn)
            pis_n.append(pn)

        ps = pis_n
        ts = tis_n
    return ps, ts


def si(ai, ei, ps, ts):
    return sum([pk * fij(ai, ei, tk) for pk, tk in zip(ps, ts)])


def tj(ages, pj, to, ps, ts):
    n = len(ages)

    pj = 1 / n * sum([pj * fij(ai, ei, to) / si(ai, ei, ps, ts) for ai, ei in ages])
    a = [pj * ai * fij(ai, ei, to) / (ei**2 * si(ai, ei, ps, ts)) for ai, ei in ages]
    b = [pj * fij(ai, ei, to) / (ei**2 * si(ai, ei, ps, ts)) for ai, ei in ages]

    return pj, sum(a) / sum(b)


def fij(ai, ei, tj):
    return 1 / (ei * sqrt(2 * pi)) * exp(-((ai - tj) ** 2) / (2 * ei**2))


if __name__ == "__main__":
    # [35.27,36.27] [0.59, 0.41]
    # p = '/Users/ross/Sandbox/unmix_data.txt'
    # with open(p, 'U') as rfile:
    #     reader = csv.reader(rfile, delimiter='\t')
    #     ages, errors = [], []
    #
    #     for line in reader:
    #         age = float(line[0])
    #         error = float(line[1])
    #         ages.append(age)
    #         errors.append(error)

    # a = np.random.normal(35, 1, 10)
    # b = np.random.normal(35, 1, 10)
    # c = np.random.normal(35, 1, 10)
    # for ai, aj, ak in zip(a, b, c):
    #     ps = np.random.random_sample(3)
    #     t = ps.sum()
    #     ps = ps / t
    #
    #     initial_guess = [[ai, aj, ak], ps]
    #     #        print 'initial', initial_guess
    #     #    initial_guess = [[30, 40], [0.9, 0.1]]
    #     print(unmix(ages, errors, initial_guess))

    a = normal(35, 0.1, 10)
    b = normal(35.5, 0.1, 10)
    ages = hstack((a, b))
    errors = [0.1] * 20

    ts = [35, 35.5]
    ps = [0.9, 0.1]

    plt.plot(sorted(a), arange(10), "bo")
    plt.plot(sorted(b), arange(10, 20, 1), "ro")
    print(unmix(ages, errors, ps, ts))
    plt.show()
# ============= EOF =============================================
