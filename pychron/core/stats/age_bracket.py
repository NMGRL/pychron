# ===============================================================================
# Copyright 2017 ross
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

def get_data_test():
    h = [20, 0]
    t = [2, 12]
    e = [0.1, 1]
    e = [1, 0.1]

    return h, t, e


def get_data3():
    h = [0, 178]
    t = [74.11, 73.37]
    e = [0.62 / 2., 0.18 / 2.]

    return h, t, e


def get_data1():
    h = [178, 0]
    t = [73.37, 74.11]
    e = [0.18 / 2, 0.62 / 2]

    return h, t, e


def get_data2():
    h = [76, 0]
    t = [3.28, 3.40]
    e = [0.04, 0.03]
    return h, t, e


def interpolate2(y, t, e, yp):
    """
    from below
    :param y:
    :param t:
    :param e:
    :param yp:
    :return:
    """

    dt = t[1] - t[0]
    dyp = yp - y[1]
    dy = y[1] - y[0]
    tp = t[1] + dt * dyp / dy

    a = dyp / dy
    b = 1 - a
    c = dt * dyp / (dy ** 2)
    d = dt / dy
    sy = 0.1 * dy
    syp = 0.1 * dyp
    e1 = ((a * e[0]) ** 2 + (b * e[1] ** 2) + (c * sy) ** 2 + (d * syp) ** 2) ** 0.5

    dyp = y[0] - yp
    dy = y[0] - y[1]
    ee = dyp / dy
    f = 1 - ee
    g = dt * dyp / (dy ** 2)
    e2 = ((ee * e[1]) ** 2 + (f * e[0] ** 2) + (g * sy) ** 2 + (d * syp) ** 2) ** 0.5
    return tp, e1, e2


def interpolate(y, t, e, yp):
    t1 = t[0]
    dt = t[1] - t[0]
    dyp = y[0] - yp
    dy = y[1] - y[0]

    tp = t1 - dt * dyp / dy

    # sy = 0.1 * dy
    sy = 0.1 * dy
    # sy = 0
    syp = 0.1 * dyp
    # syp = 0
    d = dt / dy

    ee = dyp / dy
    f = 1 - ee
    g = dt * dyp / dy ** 2
    # sy = 0.1 * dy
    # syp = 0.1 * dyp
    ep = ((ee * e[1]) ** 2 + (f * e[0]) ** 2 + (g * sy) ** 2 + (d * syp) ** 2) ** 0.5
    ep3 = ((ee * e[0]) ** 2 + (f * e[1]) ** 2 + (g * sy) ** 2 + (d * syp) ** 2) ** 0.5
    #
    a = dyp / dy
    b = 1 - a
    c = dt * dyp / dy ** 2
    ep2 = ((a * e[0]) ** 2 + (b * e[1]) ** 2 + (c * sy) ** 2 + (d * syp) ** 2) ** 0.5
    ep4 = ((a * e[1]) ** 2 + (b * e[0]) ** 2 + (c * sy) ** 2 + (d * syp) ** 2) ** 0.5
    return tp, ep , ep3, ep2, ep4


y, t, e = get_data_test()
# print interpolate(y, t, e, .75)
# print interpolate(y, t, e, .5)
# print interpolate(y, t, e, .25)
print 'from above'
print 'height=0',
print interpolate(y, t, e, 0)
print 'height=10',
print interpolate(y, t, e, 10)
print 'height=20',
print interpolate(y, t, e, 20)

print 'from below'
print 'height=0',
print interpolate2(y, t, e, 0)
print 'height=10',
print interpolate2(y, t, e, 10)
print 'height=20',
print interpolate2(y, t, e, 20)

# y, t, e = get_data1()
# print interpolate(y, t, e, 147)
# #
y, t, e = get_data2()
print interpolate(y, t, e, 56)
y, t, e = get_data2()
print interpolate2(y, t, e, 56)
# print interpolate(y, t, e, 35)
#
# y, t, e = get_data3()
# print interpolate2(y, t, e, 147)
# ============= EOF =============================================
