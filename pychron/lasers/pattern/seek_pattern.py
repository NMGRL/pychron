# ===============================================================================
# Copyright 2011 Jake Ross
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
from chaco.default_colormaps import hot
from traits.api import List, Float, Int, Enum
from traitsui.api import View, Item
# ============= standard library imports ========================
import math
import time
from collections import defaultdict
from numpy import random, copy, average, polyfit, arange, linspace, hstack
# ============= local library imports  ==========================
from pychron.lasers.pattern.patterns import Pattern
from pychron.mv.lumen_detector import LumenDetector


def rotate(x, y, center=(0, 0), theta=0):
    dx = x - center[0]
    dy = y - center[1]

    nx = dx * math.cos(theta) - dy * math.sin(theta)
    ny = dy * math.cos(theta) + dx * math.sin(theta)
    return nx, ny


def calculate_center(ps):
    pts = sorted(ps, key=lambda p: p[1])
    (x1, y1), (x2, y2) = pts[:2]
    dy, dx = (y2 - y1), (x2 - x1)
    theta = math.atan2(dy, dx)
    base = (dy ** 2 + dx ** 2) ** 0.5

    spts = [rotate(*p, theta=-theta) for p in pts]

    x1, y1 = spts[0]
    b2 = base / 2.
    height = 3 ** 0.5 / 2 * base
    bx = x1 + b2
    by = y1 + 1 / 3. * height

    cx, cy = rotate(bx, by, theta=theta)
    return cx, cy


def triangulator(pts, side):
    """
    pts should be reverse sorted by score

    :param pts: 3-tuple (score, x,y)
    :param side:
    :return:
    """
    pt1, pt2, pt3 = pts
    x1, y1 = pt1[1], pt1[2]
    x2, y2 = pt2[1], pt2[2]
    ox, oy = pt3[1], pt3[2]

    mx = (x1 + x2) / 2.
    my = (y1 + y2) / 2.

    v1 = mx - ox
    v2 = my - oy
    l = (v1 ** 2 + v2 ** 2) ** 0.5

    try:
        ux, uy = v1 / l, v2 / l
    except ZeroDivisionError:
        ux, uy = 0, 0

    nx = mx + side * ux
    ny = my + side * uy
    return nx, ny, ox, oy


def height(b):
    return (3 ** 0.5) / 2. * b


class Point:
    def __init__(self, x, y, score=0):
        self.x, self.y = x, y
        self.score = score

    def totuple(self):
        return self.score, self.x, self.y


class Triangle:
    scalar = 1.0
    _point_cnts = None

    def __init__(self, base):
        self._base = base
        h = height(base)
        self._height = h

        self._points = [Point(0, 0), Point(base, 0), Point(base / 2., h)]

        self.clear_point_cnts()

    def set_point(self, score, x, y, idx=None):
        if idx is None:
            pt = self.get_point(x, y)
            if pt:
                pt.score = score
            else:
                self._points.append(Point(x, y, score))
        else:
            self._points[idx] = Point(x, y, score)

    def get_point(self, x, y):
        return next((p for p in self._points if abs(p.x - x) < 1e-6 and abs(p.y - y) < 1e-6), None)

    def point_xy(self, idx=None):
        if idx is None:

            pts = sorted([p.totuple() for p in self._points], reverse=True)
            x, y, rx, ry = triangulator(pts, self._height)

            pt = self.get_point(rx, ry)
            self._points.remove(pt)

        else:
            pt = self._points[idx]
            x, y = pt.x, pt.y

        self._point_cnts[(x, y)] += 1
        return x, y

    def point_cnt(self, pt):
        return self._point_cnts[pt]

    def clear_point_cnts(self):
        self._point_cnts = defaultdict(int)

    def weighted_centroid(self):
        weights, xps, yps = zip(*[(p.score, p.x, p.y) for p in self._points])
        cx = average(xps, weights=weights)
        cy = average(yps, weights=weights)
        return self.centered(cx, cy)

    def centered(self, cx, cy):
        base = self.base
        h = self._height
        x1 = cx - (1 / 2.) * base
        x2 = cx + (1 / 2.) * base
        x3 = cx

        y1 = cy - (1 / 3.) * h
        y2 = y1
        y3 = cy + (2 / 3.) * h

        self._points = [Point(x1, y1), Point(x2, y2), Point(x3, y3)]
        return (x1, y1), (x2, y2), (x3, y3)

    def set_scalar(self, s):
        self.scalar = s
        self._height = height(self.base)

    @property
    def base(self):
        return self.scalar * self._base

    def xys(self):
        return [(p.x, p.y, p.score) for p in self._points]

    def is_equilateral(self):

        p1, p2, p3 = self._points
        d1 = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
        d2 = ((p1.x - p3.x) ** 2 + (p1.y - p3.y) ** 2) ** 0.5
        d3 = ((p2.x - p3.x) ** 2 + (p2.y - p3.y) ** 2) ** 0.5
        # print d1, d2, d3, abs(d1 - d2) < 1e-4 and abs(d1 - d3) < 1e-4
        return abs(d1 - d2) < 1e-4 and abs(d1 - d3) < 1e-4


class SeekPattern(Pattern):
    total_duration = 30
    duration = Float(0.1)
    base = Float(0.5)
    perimeter_radius = Float(2.5)
    limit = Int(10)
    pre_seek_delay = Float(0.25)
    saturation_threshold = Float(0.75)

    mask_kind = Enum('Hole', 'Beam', 'Custom')
    custom_mask_radius = Float

    _points = List
    _data = List

    def point_generator(self):
        def gen():

            self._tri = tri = Triangle(self.base)

            yield tri.point_xy(0)
            yield tri.point_xy(1)
            yield tri.point_xy(2)

            while 1:
                if tri.scalar < 1:
                    n = len(self._data)
                    if n > 5:
                        m, b = polyfit(arange(n), self._data, 1)
                        if m < 0:
                            tri.clear_point_cnts()
                            tri.set_scalar(1)
                            # construct a new triangle centered at weighted centroid of current points
                            # weighted by score
                            p1, p2, p3 = tri.weighted_centroid()
                            yield p1
                            yield p2
                            yield p3

                            continue

                x, y = tri.point_xy()
                if tri.point_cnt((x, y)) > 5:
                    self._data = []
                    tri.clear_point_cnts()
                    tri.set_scalar(0.5)
                    # construct a new triangle centered at weighted centroid of current points
                    # weighted by score
                    p1, p2, p3 = tri.centered(x, y)
                    yield p1
                    yield p2
                    yield p3

                    continue

                if not self._validate(x, y):
                    tri = Triangle(self.base)
                    yield tri.point_xy(0)
                    yield tri.point_xy(1)
                    yield tri.point_xy(2)
                    continue

                yield x, y

        return gen()

    def _validate(self, x, y):
        return (x ** 2 + y ** 2) ** 0.5 <= self.perimeter_radius

    def update_point(self, score, x, y, idx=-1):
        """
        average score with the current score for this point.
        weight values by time. the more negative idx the less weight
        """
        w1, w2 = 1, 1
        if idx == -1:
            w1, w2 = 0.75, 1.25
        elif idx == -2:
            w1, w2 = 0.50, 1.5
        elif idx == -3:
            w1, w2 = 0.25, 1.75

        v = (w1 * self._data[idx] + w2 * score) / 2.
        self._data[idx] = v
        self._tri.set_point(v, x, y, idx)

    def set_point(self, z, x, y):
        self._data.append(z)
        self._data = self._data[-self.limit:]

        self._tri.set_point(z, x, y)

    def maker_view(self):
        v = View(Item('total_duration', label='Total Duration (s)',
                      tooltip='Total duration of search (in seconds)'),
                 Item('duration',
                      label='Dwell Duration (s)',
                      tooltip='Amount of time (in seconds) to wait at each point. '
                              'The brightness value is average of all measurements taken '
                              'while moving AND waiting at the vertex'),
                 Item('pre_seek_delay', label='Pre Search Delay (s)',
                      tooltip='Turn laser on and wait N seconds before starting search'),
                 Item('velocity',
                      label='Velocity (mm/s)'),
                 Item('perimeter_radius',
                      label='Perimeter Radius (mm)',
                      tooltip='Limit the search to a circular area with this radius (in mm)'),
                 Item('base',
                      label='Side (mm)',
                      tooltip="Length (in mm) of the search triangle's side"),
                 Item('saturation_threshold', label='Saturation Threshold',
                      tooltip='If the saturation score is greater than X then do not move'),
                 Item('mask_kind', label='Mask', tooltip="Define the lumen detector's mask as Hole, Beam, Custom."
                                                         "Beam= Beam radius + 10%\n"
                                                         "Hole= Hole radius"),
                 Item('custom_mask_radius', label='Mask Radius (mm)',
                      visible_when='mask_kind=="Custom"'))
        return v

    def replot(self):
        pass

    def calculate_transit_time(self):
        pass


def test1():
    from numpy import zeros, ogrid
    import matplotlib

    matplotlib.use('Qt4Agg')

    from matplotlib.animation import FuncAnimation
    import matplotlib.pyplot as plt

    class FrameGenerator:
        def __init__(self):
            self.width = 300
            self.height = 300
            self.ox = 150
            self.oy = 150
            self.radius = 75
            self.laser_x = 0
            self.laser_y = 0
            self.random_walk = False
            self._cnt = 0
            self.time_constant = 0
            self.cradius = 0

        def __iter__(self):
            self._cnt = 0
            return self

        def set_pos(self, x, y):
            self.laser_x = x
            self.laser_y = y
            self.ox = x
            self.oy = y

        def _calculate_radius(self):
            f = ((self.laser_x - self.width / 2.) ** 2 + (self.laser_y - self.height / 2.) ** 2) ** 0.5
            # g = 50*math.sin(0.1*self._cnt)
            # g = 1+math.sin(0.1*self._cnt)
            # print self._cnt, g

            g = min(1, (1 - (50 - self._cnt) / 50.))

            h = 0 + 15 * math.sin(0.1 * self._cnt) if self._cnt > 50 else 0
            self.time_constant = h
            rr = self.radius * g + h
            self._cnt += 1
            r = int(max(1, rr * (150 - f) / 150.))  # +random.randint(0,10)
            self.cradius = r
            return r
            # return self.radius * max(0.001, (1-f/self.radius))
            # try:
            #     ff = 5/float(f)
            # except ZeroDivisionError:
            #     ff = 1
            # print f, 1/f
            # ff = f/self.
            # return int(self.radius*ff)

        def next(self):
            radius = self._calculate_radius()
            offset = 3
            src = zeros((self.width, self.height))

            d = (0, 0)
            if self.random_walk:
                d = random.uniform(-offset, offset, 2)

            cx = self.ox + d[0]
            cy = self.oy + d[1]

            # if ((cx - 100) ** 2 + (cy - 100) ** 2) ** 0.5 > 50:
            #     dx = offset if cx < 0 else -offset
            #     dy = offset if cy < 0 else -offset
            #     cx += dx
            #     cy += dy
            # rain_drops['position'][current_index] += dx,dy

            # self.ox = cx
            # self.oy = cy
            y, x = ogrid[-radius:radius, -radius:radius]
            index = x ** 2 + y ** 2 <= radius ** 2

            # src[cy - radius:cy + radius, cx - radius:cx + radius][index] = 255*random.uniform(size=index.shape)
            src[cy - radius:cy + radius, cx - radius:cx + radius][index] = 255
            # xx, yy = mgrid[:200, :200]
            # circles contains the squared distance to the (100, 100) point
            # we are just using the circle equation learnt at school
            # circle = (xx - 100) ** 2 + (yy - 100) ** 2
            # print circle.shape
            # print circle
            # raise  StopIteration
            return src

    ld = LumenDetector()
    ld.hole_radius = 2
    fig, ((ax, ax2,), (ax3, ax4), (ax5, ax6),
          (ax7, ax8)) = plt.subplots(4, 2, figsize=(7, 7))

    f = FrameGenerator()
    pattern = SeekPattern(base=15, perimeter_radius=100)
    o = f.next()

    ax.set_title('Current Frame')
    img = ax.imshow(o)

    gen = pattern.point_generator()

    ax2.set_title('Observed Brightness')
    img2 = ax2.imshow(o)

    ax3.set_title('Position')
    line = ax3.plot([0], [0])[0]

    r = pattern.perimeter_radius
    xs = linspace(-r, r)
    xs2 = xs[::-1]
    ys = (r ** 2 - xs ** 2) ** 0.5
    ys2 = -(r ** 2 - xs2 ** 2) ** 0.5
    xxx, yyy = hstack((xs, xs2)) + 150, hstack((ys, ys2)) + 150
    # print xxx,yyy
    # print xs+150, ys+150
    # ax3.plot(xs+150,ys+150)
    ax3.plot(xxx, yyy)

    ax3.set_xlim(50, 250)
    ax3.set_ylim(50, 250)
    scatter = ax3.plot([150], [150], '+')

    xx, yy = 100, 150
    scatter2 = ax3.plot([xx], [yy], 'o')[0]

    cp = ax7.scatter([0], [0], c=[0])
    cp.autoscale()
    ax7.set_xlim(-100, 100)
    ax7.set_ylim(-100, 100)

    ax4.set_title('Intensity')
    tvint = ax4.plot([1], [1])[0]
    # tvint = ax4.semilogy([1],[1])[0]
    ax4.set_xlim(0, 50)
    # ax4.set_ylim(0, 1.1)

    ax5.set_title('Time Constant')
    tc = ax5.plot([0], [0])[0]
    ax5.set_ylim(-20, 20)
    ax5.set_xlim(0, 50)

    ax5.set_title('Radius')
    rs = ax6.plot([0], [0])[0]
    ax6.set_ylim(0, 100)
    ax6.set_xlim(0, 50)

    xs = []
    ys = []
    ts = []
    zs = []
    tcs = []
    rcs = []
    f.set_pos(xx, yy)
    st = time.time()

    def update(frame_number):
        # print frame_number
        x, y = gen.next()
        f.set_pos(xx + x, yy + y)
        # f.set_pos(frame_number,100)
        src = f.next()
        img.set_array(src)

        a, z = ld.get_value(copy(src))
        # print x,y, z
        img2.set_array(a)
        # print z, x, y
        xs.append(xx + x)
        ys.append(yy + y)
        line.set_data(xs, ys)
        scatter2.set_data([xx + x], [yy + y])

        ts.append(time.time() - st)
        # print z
        # z /= 3716625.0
        # z += 0.1 * random.random()
        # print x, y, z
        pattern.set_point(z, x, y)
        zs.append(z)
        # print ts
        # print zs
        tvint.set_data(ts, zs)
        ax4.set_ylim(min(zs) * 0.9, max(zs) * 1.1)

        tcs.append(f.time_constant)
        rcs.append(f.cradius)
        tc.set_data(ts, tcs)

        rs.set_data(ts, rcs)

        # >>>>>>>>>>>>>>>>>>>>>>>
        # add a plot that is the current points of the triangle
        # >>>>>>>>>>>>>>>>>>>>>>>
        xy = pattern._tri.xys()
        x, y, z = zip(*xy)
        # print x, y
        # cp.set_data(x, y)
        cp.set_offsets(zip(x, y))

        maz, miz = max(z), min(z)
        z = [(zi - miz) / (maz - miz) for zi in z]
        print z
        cp.set_facecolors([hot(zi) for zi in z])
        # cp.set_edgecolors(z)
        if not pattern._tri.is_equilateral():
            print 'not eq'

            # return mplfig_to_npimage(fig)
            # raw_input()

    animation = FuncAnimation(fig, update, interval=1000)
    plt.show()

    # duration = 30
    # animation = mpy.VideoClip(update, duration=duration)
    # animation.write_gif("/Users/ross/Desktop/seek2.gif", fps=5)


def test_trianglator():
    import matplotlib

    matplotlib.use('Qt4Agg')

    h = 3 ** 0.5 / 2.
    print 'height', h
    pts = [(0, 0, 0), (10, 1, 0), (20, 0.5, h)]
    pts = sorted(pts, reverse=True)
    import matplotlib.pyplot as plt
    x, y = triangulator(pts, h)
    zs, xs, ys = zip(*pts)
    plt.xlim(-1, 3)
    plt.ylim(-1, 3)

    plt.plot(xs, ys)
    print x, y
    plt.plot([x], [y], 'o')
    plt.show()


if __name__ == '__main__':
    # test_trianglator()
    test1()
