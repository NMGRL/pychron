# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
from __future__ import absolute_import
from __future__ import print_function
from numpy import linspace
from scipy.optimize import leastsq
from scipy.stats import norm

# ============= local library imports  ==========================
import matplotlib.pyplot as plt


# def res(p, y, x):
#     h1, h2, m1, m2, sd1, sd2 = p
#     # m, dm, sd1, sd2 = p
#     # m1 = m
#     # m2 = m1 + dm
#     y_fit = h1 * norm.pdf(x, m1, sd1) + h2 * norm.pdf(x, m2, sd2)
#     err = y - y_fit
#     return err
#
#
# p = [1, 1, 5, 10, 1, 1]
# plsq = leastsq(res, p, args=(sys3, xs))


def res(p, y, x):
    yfit = None
    n = p.shape[0] / 3
    for h, m, s in p.reshape(n, 3):
        yi = h * norm.pdf(x, m, s)
        if yfit is None:
            yfit = yi
        else:
            yfit += yi
    err = y - yfit
    return err


def demo():
    n = 500
    xs = linspace(0, 10, n)
    ys = 2 * norm.pdf(xs, 5, 0.5)  # +0.01*random(n)
    ys2 = norm.pdf(xs, 6.1, 0.5)  # +0.01*random(n)
    ys3 = norm.pdf(xs, 4.5, 0.5)  # +0.01*random(n)

    sys3 = ys + ys2 + ys3

    plt.plot(xs, ys)
    plt.plot(xs, ys2)
    plt.plot(xs, ys3)
    plt.plot(xs, sys3)

    mm = sys3.argmax()
    mm = xs[mm]
    p = [(1, mm, 1), (1, mm, 1), (1, mm, 1)]
    plsq = leastsq(res, p, args=(sys3, xs))
    print(plsq)
    plt.vlines(plsq[0][1], 0, 1.8)
    plt.vlines(plsq[0][4], 0, 1.8)
    plt.vlines(plsq[0][7], 0, 1.8)
    plt.show()


if __name__ == "__main__":
    demo()
# ============= EOF =============================================
