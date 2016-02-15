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
from traits.api import List, Float, Int
from traitsui.api import View, Item
# ============= standard library imports ========================
import math
import time
from numpy import random, copy, polyfit, arange
# ============= local library imports  ==========================
from pychron.lasers.pattern.patterns import Pattern
from pychron.mv.lumen_detector import LumenDetector


def triangulator(pts, base, scalar=1):
    st = sorted(pts, reverse=True)
    pt1 = st[0]
    pt2 = st[1]
    pt3 = st[2]

    x1, y1 = pt1[1], pt1[2]
    x2, y2 = pt2[1], pt2[2]
    ox, oy = pt3[1], pt3[2]

    mx = (x1 + x2) / 2.
    my = (y1 + y2) / 2.

    v1 = mx - ox
    v2 = my - oy
    # print v1,v2
    l = (v1 ** 2 + v2 ** 2) ** 0.5
    try:
        ux, uy = v1 / l, v2 / l
    except ZeroDivisionError:
        ux, uy = 0, 0

    nx = mx + base * scalar * ux
    ny = my + base * scalar * uy
    return nx, ny


class SeekPattern(Pattern):
    duration = Float(0.1)
    base = Float(0.5)
    perimeter_radius = Float(5)
    limit = Int(10)

    _previous_pt = None
    _points = List
    _data = List

    def point_generator(self):
        def rotate(x, y, px):
            # offpeak_cnt += 1
            theta = math.radians(15)  # random.randint(-180, 180))
            if len(px) == 3:
                ox, oy = px[1][0], px[1][1]
            else:
                ox, oy = 0, 0
            nx = math.cos(theta) * (x - ox) - math.sin(theta) * (y - oy) + ox
            ny = math.sin(theta) * (x - ox) + math.cos(theta) * (y - oy) + oy
            # print x, nx, ox, y, ny, oy
            return nx, ny

        def gen():
            yield 0, 0
            yield self.base, 0
            yield self.base / 2., self.base

            px = []
            scalar = 1.0
            offpeak_cnt = 0
            while 1:

                x, y = triangulator(self._points, self.base, scalar=scalar)

                st = sorted(self._points, reverse=True)
                st.pop(-1)
                self._points = st

                px.append((x, y))
                px = px[-3:]

                m = 1
                if len(self._data) == self.limit:
                    m, b = polyfit(arange(len(self._data)), self._data, 1)

                repeat_point = (len(px) == 3 and px[0] == px[2])

                if m < 0:
                    scalar = 1.0
                    x, y = rotate(x, y, px)
                elif repeat_point:
                    scalar *= 0.5
                    x, y = rotate(x, y, px)

                if not self._validate(x, y):
                    x, y = self.cx, self.cy

                yield x, y

        return gen()

    def _validate(self, x, y):
        return ((x ** 2 - self.cy) + (y - self.cy) ** 2) ** 0.5 <= self.perimeter_radius

    def set_point(self, z, x, y):
        self._data.append(z)
        self._data = self._data[-self.limit:]
        self._points.append((z, x, y))

    def maker_view(self):
        v = View(Item('duration',
                      label='Duration (s)',
                      tooltip='Amount of time (in seconds) to wait at each point. '
                              'The brightness value is average of all measurements taken '
                              'while moving AND waiting at the vertex'),
                 Item('velocity',
                      label='Velocity (mm/s)'),
                 Item('perimeter_radius',
                      label='Perimeter Radius (mm)',
                      tooltip='Limit the search to a circular area with this radius (in mm)'),
                 Item('base',
                      label='Base (mm)',
                      tooltip="Length (in mm) of the search triangle's base"))
        return v

    def replot(self):
        pass

    def calculate_transit_time(self):
        pass


if __name__ == '__main__':
    from numpy import zeros, ogrid
    import matplotlib

    matplotlib.use('Qt4Agg')

    from moviepy.video.io.bindings import mplfig_to_npimage
    import moviepy.editor as mpy


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


    # crop_width = 2
    # crop_height = 2
    ld = LumenDetector()

    # def get_brightness(src):
    #     # ld = self._lumen_detector
    #     # cw, ch = 2 * crop_width * self.pxpermm, 2 * self.crop_height * self.pxpermm
    #     # src = self.video.get_frame()
    #     # src = crop_image(src, 200,200)
    #     # if src:
    #     # else:
    #     #     src = random.random((ch, cw)) * 255
    #     #     src = src.astype('uint8')
    #     #         return random.random()
    #     src, v = ld.get_value(src)
    #     return v


    import matplotlib.pyplot as plt

    # pts = [(20, 0, 0), (20, 10, 0), (10, 5, 10)]
    # nx, ny = triangulator(pts)
    # print nx, ny
    # import matplotlib.pyplot as plt
    #
    # pts = [(0, 0), (10, 0), (5, 10)]
    # xs = [0, 10, 5, 0]
    # ys = [0, 0, 10, 0]
    # plt.plot(xs, ys)
    # plt.plot([nx], [ny], 'o')
    # plt.xlim(-25, 25)
    # plt.ylim(-25, 25)
    # plt.show()
    # show()
    # fig = plt.figure(figsize=(7, 7))
    # fig, ((ax, ax2, ax3),(ax4, ax5, ax6)) = plt.subplots(6, 2, figsize=(7, 7))
    fig, ((ax, ax2,), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(7, 7))
    # ax = plt.subplot(411)
    # ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    # ax2 = fig.add_axes([0, 0, 1, 1], frameon=False)
    # ax.set_xlim(-1,1), ax.set_xticks([])
    # ax.set_ylim(-1,1), ax.set_yticks([])
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
    ax3.set_xlim(0, 300)
    ax3.set_ylim(0, 300)
    scatter = ax3.plot([150], [150], '+')

    xx, yy = 100, 150
    scatter2 = ax3.plot([xx], [yy], 'o')[0]

    ax4.set_title('Intensity')
    tvint = ax4.plot([1], [1])[0]
    # tvint = ax4.semilogy([1],[1])[0]
    ax4.set_xlim(0, 50)
    ax4.set_ylim(0, 1.1)

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
        z /= 3716625.0
        # z += 0.1 * random.random()

        pattern.set_point(z, x, y)
        zs.append(z)
        # print zs
        tvint.set_data(ts, zs)

        tcs.append(f.time_constant)
        rcs.append(f.cradius)
        tc.set_data(ts, tcs)

        rs.set_data(ts, rcs)
        return mplfig_to_npimage(fig)
        # raw_input()


    # animation = FuncAnimation(fig, update, interval=50)
    # plt.show()

    duration = 30
    animation = mpy.VideoClip(update, duration=duration)
    animation.write_gif("/Users/ross/Desktop/seek2.gif", fps=5)
