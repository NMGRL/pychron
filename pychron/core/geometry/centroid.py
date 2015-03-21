# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= local library imports  ==========================
# import numpy as np
# cimport numpy as np
# def _area(np.ndarray[np.float64_t, ndim=2] data):
def _area(data):
#    cdef int n = data.shape[0]
#    cdef int j = n - 1
#    cdef float x = 0
#    cdef float y = 0
#    cdef float a = 0

    n = data.shape[0]
    j = n - 1
    a = 0
    for i in xrange(n):
        p1 = data[i]
        p2 = data[j]
        a += (p1[0] * p2[1])
        a -= (p1[1] * p2[0])
        j = i
    return a / 2.

def calculate_centroid(data):
    n = data.shape[0]
    j = n - 1
    x = 0
    y = 0
    for i in xrange(n):
        p1 = data[i]
        p2 = data[j]
        f = p1[0] * p2[1] - p2[0] * p1[1]
        x += (p1[0] + p2[0]) * f
        y += (p1[1] + p2[1]) * f
        j = i

    a = _area(data)
    return x / (6. * a), y / (6. * a)


# ============= EOF =============================================
