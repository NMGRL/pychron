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
from numpy import array
from traits.api import List, Float
from traitsui.api import View, Item

from pychron.core.geometry.centroid import calculate_centroid
from pychron.lasers.pattern.patterns import Pattern


class SeekPattern(Pattern):
    duration = Float(0.1)
    _cnt = 0
    _points = List
    base = Float(0.5)
    perimeter_radius = Float(2)

    def next_point(self):
        if len(self._points) < 3:
            if self._cnt == 0:
                x, y = 0, 0
            elif self._cnt == 1:
                x, y = self.base, 0
            else:
                x, y = self.base / 2., self.base
            self._cnt += 1
        else:
            x, y = triangulator(self._points)

            st = sorted(pts, reverse=True)
            st.pop(-1)
            self._points = st

        if not self._validate(x, y):
            if len(self._points) < 3:
                x, y = 0, 0
            else:
                p1, p2, p3 = self._points
                x, y = calculate_centroid(array([(p1[1], p1[2]),
                                                 (p2[1], p2[2]),
                                                 (p3[1], p3[2])]))

                # if next point is outside the perimeter go to triangle center point
                # st = sorted(pts, reverse=True)
                # pt1 = st[0]
                # nx, ny = pt1[1], pt1[2]
        return x, y
        # nx, ny = self.cx + x, self.cy + y
        # return nx, ny

    def _validate(self, x, y):
        return (x ** 2 + y ** 2) ** 0.5 < self.perimeter_radius

    def set_point(self, z, x, y):
        self._points.append((z, x - self.cx, y - self.cy))

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


def triangulator(pts):
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
    l = (v1 ** 2 + v2 ** 2) ** 0.5
    ux, uy = v1 / l, v2 / l

    nx = mx + l * ux
    ny = my + l * uy
    return nx, ny


if __name__ == '__main__':
    pts = [(0, 0, 0), (20, 10, 0), (10, 5, 10)]
    nx, ny = triangulator(pts)
    import matplotlib.pyplot as plt

    pts = [(0, 0), (10, 0), (5, 10)]
    xs = [0, 10, 5, 0]
    ys = [0, 0, 10, 0]
    plt.plot(xs, ys)
    plt.plot([nx], [ny], 'o')
    plt.xlim(-1, 25)
    plt.ylim(-1, 25)
    plt.show()
