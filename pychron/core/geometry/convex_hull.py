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
"""
http://www.scipy.org/Cookbook/Finding_Convex_Hull
"""

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from numpy import arctan, pi, cross, asarray, apply_along_axis, arange
from numpy.linalg import norm


def _angle_to_point(point, centre):
    """calculate angle in 2-D between points and x axis"""
    delta = point - centre
    res = arctan(delta[1] / delta[0])
    if delta[0] < 0:
        res += pi
    return res


def area_of_triangle(p1, p2, p3):
    """calculate area of any triangle given co-ordinates of the corners"""
    return norm(cross((p2 - p1), (p3 - p1))) / 2.0


def convex_hull(points):
    """Calculate subset of points that make a convex hull around points

    Recursively eliminates points that lie inside two neighbouring points until only convex hull is remaining.

    :Parameters:
        points : ndarray (2 x m)
            array of points for which to find hull
        graphic : bool
            use pylab to show progress?

    :Returns:
        hull_points : ndarray (2 x np)
            convex hull surrounding points"""

    #    if not isinstance(points[0], (tuple, np.ndarray)):
    #        points = [(pi.x, pi.y) for pi in points]

    points = asarray(points)
    points = points.T
    n_pts = points.shape[1]
    assert n_pts > 1
    centre = points.mean(1)
    angles = apply_along_axis(_angle_to_point, 0, points, centre)
    pts_ord = points[:, angles.argsort()]

    pts = [x[0] for x in zip(pts_ord.transpose())]
    prev_pts = len(pts) + 1
    while prev_pts > n_pts:
        prev_pts = n_pts
        n_pts = len(pts)
        i = -2
        while i < (n_pts - 2):
            Aij = area_of_triangle(centre, pts[i], pts[(i + 1) % n_pts])
            Ajk = area_of_triangle(centre, pts[(i + 1) % n_pts], pts[(i + 2) % n_pts])
            Aik = area_of_triangle(centre, pts[i], pts[(i + 2) % n_pts])
            if Aij + Ajk < Aik:
                del pts[i + 1]
            i += 1
            n_pts = len(pts)
    return asarray(pts)


def convex_hull_area(pts):
    """
    http://en.wikipedia.org/wiki/Polygon#Area_and_centroid
    """
    from pychron.core.codetools.simple_timeit import timethis

    hull = timethis(convex_hull, args=(pts,))
    #    hull = convex_hull(pts)
    x, y = list(zip(*hull))
    ind_arr = arange(len(x)) - 1  # for indexing convenience
    s = sum([x[ii] * y[ii + 1] - x[ii + 1] * y[ii] for ii in ind_arr])
    return abs(s) * 0.5


# ============= EOF =============================================
