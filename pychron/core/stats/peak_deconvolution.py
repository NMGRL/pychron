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
from numpy import linspace
from scipy.optimize import leastsq
from scipy.stats import norm

# ============= local library imports  ==========================
import matplotlib.pyplot as plt

n = 500
xs = linspace(0, 10, n)
ys = 2 * norm.pdf(xs, 5, 0.5)  # +0.01*random(n)
ys2 = norm.pdf(xs, 6.1, 0.5)  # +0.01*random(n)

ys3 = ys + ys2
sys3 = ys3
# sys3 = smooth(ys3)
plt.plot(xs, ys)
plt.plot(xs, ys2)
plt.plot(xs, ys3)
plt.plot(xs, sys3)


def res(p, y, x):
    h1, h2, m1, m2, sd1, sd2 = p
    # m, dm, sd1, sd2 = p
    # m1 = m
    # m2 = m1 + dm
    y_fit = h1 * norm.pdf(x, m1, sd1) + h2 * norm.pdf(x, m2, sd2)
    err = y - y_fit
    return err


p = [1, 1, 5, 10, 1, 1]
plsq = leastsq(res, p, args=(sys3, xs))
print plsq
plt.vlines(plsq[0][2], 0, 1.8)
plt.vlines(plsq[0][3], 0, 1.8)
# ye1=norm.pdf(xs, plsq[0][0], plsq[0][2])
# ye2=norm.pdf(xs, plsq[0][0] + plsq[0][1], plsq[0][3])
# plt.plot(xs, ye1)
# plt.plot(xs, ye2)

# data = []
# for xi, yi in zip(xs, ys3*100):
#     for i in xrange(int(yi)):
#         data.append(xi)
#
# yourdata = column_stack((array(data),))
# # print ys3
# # from sklearn import mixture
# # import matplotlib.pyplot as plt
# import matplotlib.mlab
# import numpy as np
# #
# # yourdata = X = column_stack((xs,))
# clf = mixture.GMM(n_components=2, covariance_type='full')
# clf.fit(yourdata)
# m1, m2 = clf.means_
# w1, w2 = clf.weights_
# c1, c2 = clf.covars_
# print m1, m2
# histdist = plt.hist(yourdata, n*10, normed=True)
# plt.vlines(m1, 0, 1.6)
# plt.vlines(m2, 0, 1.6)
# # # print histdist[1]
# # # print m1, m2
# plotgauss1 = lambda x: plt.plot(x,w1*matplotlib.mlab.normpdf(x,m1,np.sqrt(c1))[0], linewidth=3)
# plotgauss2 = lambda x: plt.plot(x,w2*matplotlib.mlab.normpdf(x,m2,np.sqrt(c2))[0], linewidth=3)
# plotgauss1(histdist[1])
# plotgauss2(histdist[1])
# plt.show()x

# unmix
# clf = mixture.GMM(n_components=2, covariance_type='full')
# X = column_stack((ys3,))
# # print X
# # print X[:,1]
# # clf.fit(X, xs)
# clf.fit(X)
# print clf.means_
# # print clf
# # m1, m2 = clf.means_
# # print m1, m2
#
# #
# max_peaks, min_peaks = find_peaks(ys3, xs, lookahead=1)
# #
# for peak in max_peaks:
#     plt.vlines(peak[0], 0, peak[1])
# #
# for peak in min_peaks:
#     plt.vlines(peak[0], 0, peak[1])
# #
plt.show()
# ============= EOF =============================================
