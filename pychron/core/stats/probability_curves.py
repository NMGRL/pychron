# ===============================================================================
# Copyright 2015 Jake Ross
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
from math import pi

from numpy import linspace, zeros, ones, exp


# ============= local library imports  ==========================


def cumulative_probability(ages, errors, xmi, xma, n=100):
    bins = linspace(xmi, xma, n)
    probs = zeros(n)

    for ai, ei in zip(ages, errors):
        if abs(ai) < 1e-10 or abs(ei) < 1e-10:
            continue

        # calculate probability curve for ai+/-ei
        # p=1/(2*pi*sigma2) *exp (-(x-u)**2)/(2*sigma2)
        # see http://en.wikipedia.org/wiki/Normal_distribution
        ds = (ones(n) * ai - bins) ** 2
        es = ones(n) * ei
        es2 = 2 * es * es
        gs = (es2 * pi) ** -0.5 * exp(-ds / es2)

        # cumulate probabilities
        # numpy element_wise addition
        probs += gs

    return bins, probs


def kernel_density(self, ages, errors, xmi, xma, n=100):
    from scipy.stats.kde import gaussian_kde

    pdf = gaussian_kde(ages)
    x = linspace(xmi, xma, n)
    y = pdf(x)

    return x, y

# ============= EOF =============================================
