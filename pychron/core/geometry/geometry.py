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

# ============= enthought library imports =======================
# ============= standard library imports ========================
import math

from numpy import (
    array,
    vstack,
    mean,
    average,
    hstack,
    zeros,
    gradient,
    asarray,
    ones_like,
    column_stack,
    ones,
)

# ============= local library imports  ==========================
from numpy.linalg import norm


# from pychron.core.geometry.centroid.calculate_centroid import calculate_centroid


def sort_clockwise(pts, xy, reverse=False):
    """
    pts = list of points
    xy = list of corresponding x,y tuples
    """
    xy = array(xy)
    # sort points clockwise
    try:
        xs, ys = xy.T
    except ValueError:
        xs, ys, _ = xy.T
    cx = xs.mean()
    cy = ys.mean()

    angles = [(math.atan2(y - cy, x - cx), pi) for pi, x, y in zip(pts, xs, ys)]
    angles = sorted(angles, key=lambda x: x[0], reverse=reverse)
    _, pts = list(zip(*angles))

    return list(pts)


#    self.points = list(pts)


def calc_point_along_line(x1, y1, x2, y2, L):
    """
    calculate pt (x,y) that is L units from x1, y1

    if calculated pt is past endpoint use endpoint


                * x2,y2
              /
            /
      L--- * x,y
      |  /
      *
    x1,y1

    L**2=(x-x1)**2+(y-y1)**2
    y=m*x+b

    0=(x-x1)**2+(m*x+b-y1)**2-L**2

    solve for x
    """
    run = x2 - x1

    if run:
        from scipy.optimize import fsolve

        m = (y2 - y1) / float(run)
        b = y2 - m * x2
        f = lambda x: (x - x1) ** 2 + (m * x + b - y1) ** 2 - L**2

        # initial guess x 1/2 between x1 and x2
        x = fsolve(f, x1 + (x2 - x1) / 2.0)[0]
        y = m * x + b

    else:
        x = x1
        if y2 > y1:
            y = y1 + L
        else:
            y = y1 - L

    lx, hx = min(x1, x2), max(x1, x2)
    ly, hy = min(y1, y2), max(y1, y2)
    if not lx <= x <= hx or not ly <= y <= hy:
        x, y = x2, y2

    return x, y


def calculate_reference_frame_center(r1, r2, R1, R2):
    """
    r1=x,y p1 in frame 1 (data space)
    r2=x,y p2 in frame 1
    R1=x,y p1 in frame 2 (screen space)
    R2=x,y p2 in frame 2

    given r1, r2, R1, R2 calculate center of frame 1 in frame 2 space
    """
    # calculate delta rotation for r1 in R2
    a1 = calc_angle(R1, R2)
    a2 = calc_angle(r1, r2)
    print(a1, a2)
    rot = 0
    #     rot = a1 - a2

    # rotate r1 to convert to frame 2
    r1Rx, r1Ry = rotate_pt(r1, rot)

    # calculate scaling i.e px/mm
    rL = calc_length(r1, r2)
    RL = calc_length(R1, R2)
    rperR = abs(RL / rL)

    print("rrrr", rL, RL)
    print(r1, r2, R1, R2)
    # calculate center
    cx = R1[0] - r1Rx * rperR
    cy = R1[1] - r1Ry * rperR

    return cx, cy, 180 - rot


def rotate_pt(pt, theta):
    pt = array([[pt[0]], [pt[1]]])

    co = math.cos(math.radians(theta))
    si = math.sin(math.radians(theta))
    R = array([[co, -si], [si, co]])
    npt = R.dot(pt)
    return npt[0, 0], npt[1, 0]


def calc_length(v1, v2):
    return norm(array(v1) - array(v2))


def calc_distances(v1, v2):
    from scipy.spatial.distance import cdist

    return cdist(v1, v2)


def calc_angle(p1, p2):
    dx = float(p1[0] - p2[0])
    dy = float(p1[1] - p2[1])
    return math.degrees(math.atan2(dy, dx))


def arc_cost_func(p, p1, p2, r):
    x0, y0 = p1
    x1, y1 = p2
    e1 = (p[0] - x0) ** 2 + (p[1] - y0) ** 2 - r**2
    e2 = (p[0] - x1) ** 2 + (p[1] - y1) ** 2 - r**2
    return [e1, e2]


def find_arc_center(p1, p2, r):
    """
    given p1, p2 of an arc with radius r find the center cx,cy of the arc

    p1: x,y
    p2: x,y
    r: radius float

    return:
        cx,cy
    """

    from scipy.optimize import fsolve

    x, info, status, message = fsolve(
        arc_cost_func, [0, 0], args=(p1, p2, r), full_output=True
    )
    if status == 1:
        return x


def approximage_polygon_center2(pts, r, weight=True):
    """
    weight by angle between p0-p1.


    :param pts:
    :param r:
    :param weight:
    :return:
    """

    n = len(pts)
    cs = zeros(n**2)

    for i, p0 in enumerate(pts):
        for j, p1 in enumerate(pts):
            cx, cy = find_arc_center(p0, p1, r)

            x0, y0 = p0[0] - cx, p0[1] - cy
            x1, y1 = p1[0] - cx, p1[1] - cy

            wi = abs(math.atan2(y1 - y0, x1 - x0) / math.pi)

            cs[i * n + j] = (cx, cy, wi)

    xs, ys, wi = cs.T
    weights = wi if weight else None

    return average(xs, weights=weights), average(ys, weights=weights)


def approximate_polygon_center(pts, r, weight=True):
    """
    given a list of polygon vertices and a known radius
    approximate the center of the polygon using the mean of xs,ys
    where xs,ys are the arc centers for different arc segments of the polygon

    if weight is true calculate a weighted mean
    where the weigthts 1/d**2 and d= distance from pt to centroid
    """

    n = len(pts)
    # cxs = []
    # cys = []

    pts = array(pts)
    pts = vstack((pts, pts))
    # for i in range(2 * n - 5):
    #     p1 = pts[i]
    #     p2 = pts[i + 4]
    m = int(n / 3)
    # for i in range(n):
    #     p1 = pts[i]
    #     p2 = pts[(i + m) % n]
    #
    #     cx, cy = find_arc_center(p1, p2, r)
    #     cxs.append(cx)
    #     cys.append(cy)

    cs = [find_arc_center(pts[i], pts[(i + m) % n], r) for i in range(n)]
    cs = [c for c in cs if c is not None]
    if cs:
        cxs, cys = zip(*cs)

        mcx = mean(cxs)
        mcy = mean(cys)

        if weight:
            # pts = sort_clockwise(pts, pts)
            #        cenx, ceny = calculate_centroid(array(pts))
            cxs = array(cxs)
            cys = array(cys)
            # weight each arc center by the inverse distance to the centroid
            #        ws = ((cxs - cenx) ** 2 + (cys - ceny) ** 2) ** -0.5
            # weight each arc center by the inverse distance to the mean
            ws = ((cxs - mcx) ** 2 + (cys - mcy) ** 2) ** -2
            mcx = average(cxs, weights=ws)
            mcy = average(cys, weights=ws)

        return mcx, mcy


TRANSPOSE = array([[0, -1], [1, 0]])


def get_intersections(p0, r0, p1, r1):
    """
    https://stackoverflow.com/questions/55816902/finding-the-intersection-of-two-circles


    :return:
    """

    x0, y0 = p0
    x1, y1 = p1

    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1
    dx = x1 - x0
    dy = y1 - y0
    d = (dx**2 + dy**2) ** 0.5
    # d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

    # non intersecting
    if d > r0 + r1:
        return None
    # One circle within other
    if d < abs(r0 - r1):
        return None
    # coincident circles
    if d == 0 and r0 == r1:
        return None
    else:
        a = (r0**2 - r1**2 + d**2) / (2 * d)
        h = (r0**2 - a**2) ** 0.5
        # h = math.sqrt(r0 ** 2 - a ** 2)
        # x2 = x0 + a * (x1 - x0) / d
        # y2 = y0 + a * (y1 - y0) / d
        # x3 = x2 + h * (y1 - y0) / d
        # y3 = y2 - h * (x1 - x0) / d
        #
        # x4 = x2 - h * (y1 - y0) / d
        # y4 = y2 + h * (x1 - x0) / d

        dxd = dx / d
        dyd = dy / d

        x2 = x0 + a * dxd
        y2 = y0 + a * dyd
        x3 = x2 + h * dyd
        y3 = y2 - h * dxd

        # x4 = x2 - h * dyd
        # y4 = y2 + h * dxd

        return x3, y3  # , x4, y4


def approximate_polygon_center3(pts, r, width, height, weight=True, k=3, freq=6):
    """
    get 2 points
    if d btw points is > 2*r skip
    find the 2 other points that make the 2 isosceles triangles with side r. This is also
    the intersection of 2 circles centers at the 2 points with radius r
    take weighted mean. weight by distance to average

    :param pts:
    :param r:
    :param weight:
    :return:
    """

    # ppts = []
    pts = pts[::freq]
    n = len(pts)
    rpts = []
    pad = 3
    m = n / k
    for i, p_i in enumerate(pts):
        j = int((i + m) % n)
        p_j = pts[j]
        if (
            pad < p_i[0] < width - pad
            and pad < p_i[1] < height - pad
            and pad < p_j[0] < width - pad
            and pad < p_j[1] < height - pad
        ):
            npts = get_intersections(p_i, r, p_j, r)
            if npts:
                # x3, y3, x4, y4 = npts
                x3, y3 = npts
                if pad < x3 < width - pad and pad < y3 < height - pad:
                    rpts.append((x3, y3))

                # if pad < x4 < width - pad and pad < y4 < height - pad:
                #     rpts.append((x4, y4))
    if rpts:
        rpts = array(rpts)
        xs = rpts[:, 0]
        ys = rpts[:, 1]
        ws = ones_like(xs)
        if weight:
            n = rpts.shape[0]
            if n > 1:
                cxs = ones(rpts.shape[0]) * xs.mean()
                cys = ones(rpts.shape[0]) * ys.mean()

                ds = calc_distances(rpts, column_stack((cxs, cys))).T[0]
                ws = 1 / ds**2

        mcx = average(xs, weights=ws)
        mcy = average(ys, weights=ws)
        return mcx, mcy, rpts


def approximate_polygon_center2(pts, r=None):
    """
    this is the ideal solution however it doesnt work as well
    as approximage_polygon_center when there are outliers

    iteratively remove points that are R from the xm,ym

    is faster and prefered approximate_polygon_center
    """

    from scipy.optimize import fmin
    from numpy import linalg

    def err(p, X, Y):
        w, v, r = p
        npts = [linalg.norm([(x - w, y - v)]) - r for x, y in zip(X, Y)]
        return (array(npts) ** 4).sum()

    def fixed_radius(p, e, X, Y):
        w, v = p
        npts = [linalg.norm([(x - w, y - v)]) - r for x, y in zip(X, Y)]
        return (array(npts) ** 2).sum()

    def make_new_point_list(p, r, tol=1):
        """
        filter points
        """
        X, Y = p.T
        xm = X.mean()
        ym = Y.mean()

        def dist(pt):
            return ((pt[0] - xm) ** 2 + (pt[1] - ym) ** 2) ** 0.5

        mask = array([dist(pp) - r < tol for pp in p], dtype=bool)
        #        print mask
        return p[mask]

    pxs = array([])
    pys = array([])
    for i in range(1000):
        # make new point list

        X, Y = pts.T
        xm = X.mean()
        ym = Y.mean()
        if r is not None:
            xf, yf = fmin(fixed_radius, [xm, ym], args=(r, X, Y), disp=False)
        else:
            xf, yf, r = fmin(err, [xm, ym, 1], args=(X, Y), disp=False)

        pts = make_new_point_list(pts, r)
        if i > 5:
            if abs(pxs.mean() - xf) < 1e-5 and abs(pys.mean() - yf) < 1e-5:
                return xf, yf, r

        pxs = hstack((pxs[-5:], xf))
        pys = hstack((pys[-5:], yf))

    return xf, yf, r


def curvature(ys):
    d = gradient(ys)
    dd = gradient(d)
    c = dd / (1 + d**2) ** 1.5
    cs = abs(c)
    return cs


def curvature_at(ys, x):
    cs = curvature(ys)
    return cs[int(x)]


if __name__ == "__main__":
    from numpy import linspace
    import matplotlib.pyplot as plt

    xs = linspace(0, 10, 100)
    ys = 1 * xs**2
    ys2 = 3 * xs**2

    plt.subplot(2, 1, 1)
    plt.plot(xs, curvature(ys))
    plt.plot(xs, curvature(ys2))
    plt.subplot(2, 1, 2)
    plt.plot(xs, ys)
    plt.plot(xs, ys2)
    plt.show()
# ============= EOF =============================================
