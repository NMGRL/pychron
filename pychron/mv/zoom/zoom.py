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
import math
import os

from scipy import stats
from skimage import feature
from skimage.transform._hough_transform import probabilistic_hough_line

# ============= standard library imports ========================
from PIL import Image
from numpy import array, linspace, \
    polyval, polyfit
import matplotlib.pyplot as plt


# ============= local library imports  ==========================


def calc_rotation(x1, y1, x2, y2):
    rise = y2 - y1
    run = x2 - x1
    return math.degrees(math.atan2(rise, run))


def calculate_spacing(p):
    # with open(p) as fp:
    im = Image.open(p).convert('L')
    w, h = im.size
    # im = im.crop((50, 50, w - 50, h - 50))
    pad = 40
    im = im.crop((pad, pad, w - pad, h - pad))

    im = array(im)

    # edges1 = feature.canny(im)
    # edges2 = feature.canny(im, sigma=3)
    edges = feature.canny(im, sigma=1)
    lines = probabilistic_hough_line(edges)
    # plot(im, edges, lines)

    xs = []
    ys = []
    for a, b in lines:
        x1, y1 = a
        x2, y2 = b
        rot = calc_rotation(x1, y1, x2, y2)

        if rot == -90.0:
            # ax2.plot((x1, x2), (y1, y2))
            # ax3.plot((x1, x2), (y1, y2))
            xs.append(x1)
            xs.append(x2)
        elif rot == 0.0:
            ys.append(y1)
            ys.append(y2)

    xs = array(sorted(xs))
    ys = array(sorted(ys))

    # print xs
    ds = []
    for xx in (xs, ys):
        for xi in xx:
            for yi in xx:
                di = yi - xi
                if di > 5:
                    ds.append(di)
                    break

    # print ds
    dists = array(ds)
    # while dists.std() > 1:
    #     md = dists.max()
    #     dists = dists[where(dists < md)]

    mr = stats.mode(dists)
    # print mr
    # print dists
    return mr.mode[0], mr.count[0], dists.mean(), dists.std()


def plot(im, edges, lines):
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3,
                                        figsize=(8,
                                                 3),
                                        sharex=True, sharey=True)

    ax1.imshow(im, cmap=plt.cm.jet)
    ax1.axis('off')

    ax2.imshow(edges, cmap=plt.cm.gray)
    ax2.axis('off')

    for a, b in lines:
        x1, y1 = a
        x2, y2 = b
        rot = calc_rotation(x1, y1, x2, y2)
        if rot == -90.0:
            ax2.plot((x1, x2), (y1, y2))
            ax3.plot((x1, x2), (y1, y2))

    fig.subplots_adjust(wspace=0.02, hspace=0.02, top=0.9,
                        bottom=0.02, left=0.02, right=0.98)

    # plt.show()


def calculate_spacings():
    ps = [
        # ('/Users/ross/Sandbox/zoom_cal/snapshot-008.jpg', 0),
        # ('/Users/ross/Sandbox/zoom_cal/snapshot-013.jpg', 0),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-007.jpg', 25, 24.958),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-012.jpg', 25, 24.958),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-014.jpg', 25, 24.965),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-006.jpg', 50, 49.997),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-011.jpg', 50, 49.993),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-002.jpg', 50, 49.916),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-015.jpg', 50, 49.909),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-005.jpg', 75, 74.986),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-003.jpg', 75, 74.941),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-016.jpg', 75, 74.937),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-010.jpg', 75, 74.979),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-009.jpg', 100, 99.955),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-004.jpg', 100, 99.969),
        ('/Users/ross/Sandbox/zoom_cal/snapshot-017.jpg', 100, 99.969),

    ]
    print 'Path        |Z   |Mode |Cnt |Avg   |STD'
    zns = [0]
    zas = [0]
    px = [23]
    for pp, zn, za in ps:
        # if z!=100:
        #     continue
        bp, _ = os.path.splitext(os.path.basename(pp))
        m, c, a, s = calculate_spacing(pp)
        a = '{:0.3f}'.format(a)
        s = '{:0.3f}'.format(s)

        print '{}|{:<4s}|{:<5s}|{:<4s}|{:<6s}|{}'.format(bp, str(zn),
                                                         str(m), str(c), a, s)
        zns.append(zn)
        zas.append(za)

        pxpermm = m / 0.25
        px.append(pxpermm)
    return zns, zas, px


if __name__ == '__main__':
    zns, zas, px = calculate_spacings()
    # print zns
    # print zas
    # print px

    # zns = [0, 25, 25, 25, 50, 50, 50, 75, 75, 75, 75, 100, 100, 100]
    # zas = [0, 24.958, 24.958, 24.965, 49.997, 49.993, 49.909, 74.986,
    #        74.941, 74.937, 74.979, 99.955, 99.969, 99.969]
    # px = [23, 28.0, 28.0, 28.0, 48.0, 48.0, 48.0, 84.0, 84.0, 84.0, 84.0,
    #       128.0, 128.0, 128.0]

    # plt.plot(zns, px, '+')
    plt.plot(zas, px, '+')
    xs = linspace(0, 100)
    # plt.plot(xs, polyval(polyfit(zns, px, 4), xs))
    coeffs = polyfit(zas, px, 4)
    print coeffs
    plt.plot(xs, polyval(coeffs, xs))
    plt.xlabel('Z')
    plt.ylabel('pxpermm')
    plt.show()
    # print os.path.basename(pp)
    # print z, calculate_spacing(pp)

# fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3,
#                                     figsize=(8,
#                                              3),
#                                     sharex=True, sharey=True)
#
# ax1.imshow(im, cmap=plt.cm.jet)
# ax1.axis('off')
#
# ax2.imshow(edges, cmap=plt.cm.gray)
# ax2.axis('off')
#
# fig.subplots_adjust(wspace=0.02, hspace=0.02, top=0.9,
#                     bottom=0.02, left=0.02, right=0.98)
#
# plt.show()
# ============= EOF =============================================
