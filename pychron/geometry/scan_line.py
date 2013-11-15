#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
# from traits.api import HasTraits
# from traitsui.api import View, Item, TableEditor
#============= standard library imports ========================
import numpy as np
import time
import math
from timeit import Timer
#============= local library imports  ==========================
from pychron.geometry.geometry import sort_clockwise
from pychron.geometry.convex_hull import convex_hull
from pychron.geometry.polygon_offset import polygon_offset

# from pylab import plot, show, text

def slope(p1, p2):
    dx = float((p2[0] - p1[0]))
    dy = float((p2[1] - p1[1]))
    if dx and dy:
        return  dx / dy  # 1/m
    else:
        return 0

def make_ET(points):
    '''
        points should be (x0,y0),(x1,y1), (x1,y1), (x2,y2),...., (xn,yn),(x0,y0)
    '''
    ET = []
    for i in range(0, len(points) - 1, 2):
        p1, p2 = points[i], points[i + 1]
        m = slope(p1, p2)
        eymin = min(p1[1], p2[1])
        eymax = max(p1[1], p2[1])
        exmin = p1[0] if p1[1] < p2[1] else p2[0]
        ET.append((m, eymin, exmin, eymax, i / 2))
    return ET

def split_vertices(points):
    '''
        return new edge table pairs
    '''
    dy = 0.1
    mpts = points[-1:] + points + points[:1]
    npts = []
    for i in range(1, len(mpts) - 1):
        pv = mpts[i - 1]
        cv = mpts[i]
        nv = mpts[i + 1]
        y = cv[1] - dy
        if pv[1] < cv[1] < nv[1]:
            cm = slope(pv, cv)
            x = pv[0] + cm * dy
            cv_prime = (x, y)
            npts.append(cv_prime)
            npts.append(cv)
        elif pv[1] > cv[1] > nv[1]:
            cm = slope(cv, nv)
            x = nv[0] + cm * dy
            cv_prime = (x, y)
            npts.append(cv)
            npts.append(cv_prime)
        else:
            npts.append(cv)
            npts.append(cv)

    npts = npts[1:] + npts[:1]
    return npts

def get_yminmax(points):
    poly = np.asarray(points)
    ys = poly[:, 1]
    ymin = np.min(ys)
    ymax = np.max(ys)
    return map(int, (ymin, ymax))

def make_scan_lines(points, step=1):
    '''
        returns a list of scan lines
        a scan line = y, xi,...xn n will always be a multiple of 2
        x,y should be integers
        
        google "scan line polygon fill algorithm example"
        www.kau.edu.sa/Files/0053697/.../Polygon%20Filling.ppt
    '''
    if not isinstance(points, list):
        points = [tuple(pi) for pi in points]

    # make points with replicates
    npts = points[:1] + [px for pi in points[1:]
                                for px in (pi, pi)] + points[:1]


    ymin, ymax = get_yminmax(points)
    scanlines = np.arange(ymin, ymax, step)

    # make Basic ET
    ET = np.array(make_ET(npts))

    # make modified ET
    nvs = split_vertices(points)

    # make ET using split vertices
    MET = np.array(make_ET(nvs))

    # copy column 0 of ET into MET
    MET[:, 0] = ET[:, 0]

    # copy last column of ET into MET
    MET[:, -1] = ET[:, -1]

    # make blank xintersections table
    xintersections = [[None for _ in range(len(MET))]
                        for _ in range(len(scanlines))]

    for m, eymin, exmin, eymax, ei in MET:
        for xint, si in zip(xintersections, scanlines):
            if eymin <= si <= eymax:
                xint[int(ei)] = exmin + m * (si - eymin)

    xs = [sorted([ii for ii in xi if ii is not None]) for xi in xintersections]
    return zip(scanlines, xs)

def make_raster_polygon(points, step=1,
                        zigzag=False):

    lines = make_scan_lines(points, step)

    npoints = []
    direction = 1
    flip = False
    # loop thru each scan line
    for yi, xs in lines:
        # traverse each x-intersection pair
#        n = len(xs)
#        if n % 2 != 0:
#            xs = sorted(list(set(xs)))

        n = len(xs)
        if n <= 1:
            continue

        if not zigzag and direction == -1:
            xs = xs[::-1]
#            xs = list(reversed(xs))

        for i in range(0, n, 2):
            try:
                x1, x2 = xs[i], xs[i + 1]
            except IndexError:
                continue
            if abs(x1 - x2) > 1e-10:
                npoints.append(((x1, yi), (x2, yi)))
                flip = True
            else:
                flip = False
        if flip:
            direction *= -1

    return npoints

def find_minimum_orientation(poly, step=1):
    P = poly.T
#    cx = np.mean(P[0])
#    cy = np.mean(P[1])

    cx, cy = get_center(poly)
    mlines = np.Inf
#    minlines = None
    lens = []
#    ms = []
    for ti in range(-90, 90, 1):
        P_prime = rotate_poly(P, ti, loc=(cx, cy))
        lines = make_raster_polygon(P_prime.T, step)
        ll = len(lines)
        if ll and ll < mlines:
            mlines = ll
            mintheta = ti
#            minlines = lines

#        ms.append(lines)
        lens.append((ti, ll))
#        print ti, 'len  ', len(lines), 'mlines  ', mlines, 'theta  ', mintheta
    o = -1
    P_prime = rotate_poly(P, mintheta - o, loc=(cx, cy))
    lines = make_raster_polygon(P_prime.T, step)
#    npoints = rotate_lines(minlines, mintheta - o, cx, cy)
    npoints = rotate_lines(lines, mintheta - o, cx, cy)
    return npoints, mintheta, lens

def rotate_lines(lines, theta, cx, cy):
    npoints = []
    for p1, p2 in lines:
        xs = [p1[0], p2[0]]
        ys = [p1[1], p2[1]]
        po = np.array([ys, xs])
        pts = rotate_poly(po, theta,
                          loc=(cy, cx)
                         )
        ys, xs = pts
        p1, p2 = (xs[0], ys[0]), (xs[1], ys[1])

        npoints.append((p1, p2))
    return npoints

def rotate_poly(pts, theta, loc=None):
    theta = math.radians(theta)
    R = np.array([[math.cos(theta), math.sin(theta)],
                  [-math.sin(theta), math.cos(theta)]])
    if loc is None:
        cx, cy = 0, 0
    else:
        cx, cy = loc[0], loc[1]

    T = np.array([[cx], [cy]])
    P_prime = R.dot(pts - T)
    P_prime = P_prime + T
    return P_prime

def get_center(pts):
    P = pts.T
    cx = np.mean(P[0])
    cy = np.mean(P[1])
    return cx, cy

def raster(poly, use_convex_hull=False,
           offset=0,
           step=1,
           find_min=False, theta=None):

    poly = np.array(poly)
    poly = sort_clockwise(poly, poly)
    if use_convex_hull:
        poly = convex_hull(poly)
    poly = np.array(poly)

    if offset:
        opoly = polygon_offset(poly, offset)
        opoly = np.array(opoly, dtype=int)
        opoly = opoly[:, (0, 1)]
    else:
        opoly = poly

    lens = []
    rtheta = 0
    if find_min:
        lines, rtheta, lens = find_minimum_orientation(opoly, step)
    else:
        lines = make_raster_polygon(opoly, step)
        if theta is not None:
            cx, cy = get_center(opoly)
            P_prime = rotate_poly(opoly.T, theta, loc=(cx, cy))
            lines = make_raster_polygon(P_prime.T, step)
            lines = rotate_lines(lines, theta, cx, cy)

    return lines, lens, rtheta


if __name__ == '__main__':
    def graph(poly, opoly, line):
        from pychron.graph.graph import Graph

        g = Graph()
        g.new_plot()

        for po in (poly, opoly):
            po = np.array(po)
            try:
                xs, ys = po.T
            except ValueError:
                xs, ys, _ = po.T
            xs = np.hstack((xs, xs[0]))
            ys = np.hstack((ys, ys[0]))
            g.new_series(xs, ys)

    #    for i, (p1, p2) in enumerate(lines):
    #        xi, yi = (p1[0], p2[0]), (p1[1], p2[1])
    #        g.new_series(xi, yi, color='black')
        return g
#    t = Timer('d()', setup='from __main__ import d')
#    print t.timeit(1)
    poly = [(2, 7), (4, 12), (8, 15), (16, 9), (11, 5), (8, 7), (5, 5)]
    poly = sort_clockwise(poly, poly)
    poly = np.array(poly)
    poly *= 1000

#    xs, ys = poly.T
#    cx, cy = xs.mean(), ys.mean()
#    poly = rotate_poly(poly.T, 45, loc=(cx, cy))
#    poly = poly.T

    use_convex_hull = False
    npoints, lens = raster(poly,
                     step=750,
                     offset=-500,
                     use_convex_hull=use_convex_hull, find_min=True)

    from pychron.graph.graph import Graph
    g = Graph(window_height=700)
    g.plotcontainer.padding = 5
    g.new_plot(padding=[60, 30, 30, 50],
               bounds=[400, 400],
               resizable='h',
               xtitle='X (microns)',
               ytitle='Y (microns)')

    if use_convex_hull:
        poly = convex_hull(poly)
        xs, ys = poly.T
        cx, cy = xs.mean(), ys.mean()
        P = poly.T
        xs = np.hstack((xs, xs[0]))
        ys = np.hstack((ys, ys[0]))
    else:
        xs, ys = poly.T
        xs = np.hstack((xs, xs[0]))
        ys = np.hstack((ys, ys[0]))

    cx, cy = xs.mean(), ys.mean()

    # plot original
    g.new_series(xs, ys)
    g.set_x_limits(min(xs), max(xs), pad='0.1')
    g.set_y_limits(min(ys), max(ys), pad='0.1')
    for ps in npoints:
        for i in range(0, len(ps), 2):
            p1, p2 = ps[i], ps[i + 1]
            g.new_series((p1[0], p2[0]),
                         (p1[1], p2[1]), color='black')

    # plot offset polygon

#    poly = sort_clockwise(poly, poly)
    opoly = polygon_offset(poly, -500)
    if use_convex_hull:
        opoly = convex_hull(opoly)
        xs, ys, _ = opoly.T
        xs = np.hstack((xs, xs[0]))
        ys = np.hstack((ys, ys[0]))
    else:
        opoly = np.array(opoly, dtype=int)
        xs, ys, _ = opoly.T

#    opoly = opoly[:, (0, 1)]
#    rpoly = rotate_poly(opoly.T, 145, loc=(cx, cy))
#    xs, ys = rpoly[0], rpoly[1]

    g.new_series(xs, ys)
    g.new_plot(padding=[50, 30, 30, 30],
               bounds=[400, 100],
               resizable='h',
               xtitle='Theta (degrees)',
               ytitle='Num. Scan Lines'
               )

    ts, ls = zip(*lens)
    g.new_series(ts, ls)

    g.configure_traits()

#============= EOF =============================================


# def d():
#    poly = [(2, 7), (4, 12), (8, 15), (16, 9), (11, 5), (8, 7), (5, 5)]
#
#
# #    poly= [(-0.7131730192833079,0.29423711121333285),
# #            (-0.4534451606058192,0.2755541205194436),
# #            (-0.2361564945226915,0.39104897208166745),
# #            (-0.22427352059627048,0.6509123880966704),
# #            (-0.5315332749794434,0.5676881568238916)]
# #    poly = [(2, 7), (4, 12), (8, 15), (16, 9), (11, 5), (8, 0), (5, 5)]
# #    poly = [(8, 15), (2, 7), (4, 12), (16, 9), (11, 5), (5, 5), (8, 7)]
# #    poly = [(1, 1), (2, 5), (5, 4), (8, 7), (10, 4), (10, 2)]
#
# #    poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
#
#    poly = np.array(poly)
#    scale = 1000
#    poly *= scale
#
#    poly = sort_clockwise(poly, poly)
# #    poly = convex_hull(poly)
#
#    opoly = polygon_offset(poly, -0.5 * scale)
#    opoly = np.array(opoly, dtype=int)
#    opoly = opoly[:, (0, 1)]
#
#    lines = make_raster_polygon(opoly, 1, int(0.5 * scale))
#    g = graph(poly, opoly, lines)
#    find_min = True
#    if find_min:
#        fscale = 200
#        fpoly = opoly / fscale
#        lines, theta = find_minimum_orientation(fpoly, int(0.5 * scale / fscale))
#
#        P = opoly.T
#        cx = np.mean(P[0])
#        cy = np.mean(P[1])
#        opoly = rotate_poly(opoly.T, theta, loc=(cx, cy))
#        lines = make_raster_polygon(opoly.T, 1, int(0.5 * scale))
#        npoints = rotate_lines(lines, theta, cx, cy)
#    else:
#        npoints = lines
#
#    for ps in npoints:
#        for i in range(0, len(ps), 2):
#            p1, p2 = ps[i], ps[i + 1]
#            g.new_series((p1[0], p2[0]),
#                         (p1[1], p2[1]), color='black')
#    return g
# #    g.configure_traits()

#    # sort et on ymin
#    ET = sorted(ET, key=lambda x: x[1])
#    buckets = []
#    cymin = ET[0][1]
#    bucket = ET[:1]
#    for m, eymin, exmin, eymax, ei in ET[1:]:
#        if eymin == cymin:
#            bucket.append((m, eymin, exmin, eymax, ei))
#        else:
#            bucket = sorted(bucket, key=lambda x:x[0], reverse=True)
#            bucket = sorted(bucket, key=lambda x:x[2], reverse=True)
#
#            buckets.append(bucket)
#            bucket = [(m, eymin, exmin, eymax, ei)]
#
#        cymin = eymin
# #        print bucket
# #        print eymin, cymin, '   ', m, eymin, exmin, eymax
#
#    buckets.append(bucket)
#    AT = []
#    for si in scanlines:
#        for bi in buckets:
#            if bi[0][1] == si:
#                AT.append(bi)
#                break
#        else:
#            AT.append(None)
# def raster_polygon(points, step=1, skip=1,
#                   move_callback=None,
#                   start_callback=None,
#                   end_callback=None,
#                   use_convex_hull=None,
#                   use_plot=False,
#                   verbose=False):
#
#    if use_convex_hull:
#        points = convex_hull(points)
#
#    points = sort_clockwise(points, points)
#
# #    print points
#    lines = make_scan_lines(points, step)
#    points = points + points[:1]
#    if use_plot:
#        from pylab import plot, text, show
#        # plot outline
#        xs, ys = zip(*points)
#        plot(xs, ys)
#
#    # initialize variables
#    cnt = 0
#    direction = 1
#    lasing = False
#
#    if verbose:
#        print 'start raster'
#
#    # loop thru each scan line
#    for yi, xs in lines[::skip]:
#        if direction == -1:
#            xs = list(reversed(xs))
#
#        # convert odd numbers lists to even
#        n = len(xs)
#        if n % 2 != 0:
#            xs = sorted(list(set(xs)))
#
#        # traverse each x-intersection pair
#        n = len(xs)
#        for i in range(0, n, 2):
#            yy = (yi, yi)
#            if len(xs) <= 1:
#                continue
#
#            xx = (xs[i], xs[i + 1])
#            if abs(xs[i] - xs[i + 1]) > 1e-10:
#                if not lasing:
#                    if verbose:
#                        print 'fast to {} {},{}'.format(cnt, xx[0], yy[0])
#                        print '===================== laser on'
#                    if move_callback is not None:
#                        move_callback(xx[0], yy[0], 'fast')
#                    if start_callback is not None:
#                        start_callback()
#
#                    lasing = True
#                else:
#                    if verbose:
#                        print 'slow to {} {},{}'.format(cnt, xx[0], yy[0])
#                    if move_callback is not None:
#                        move_callback(xx[0], yy[0], 'slow')
#
#                if verbose:
#                    print 'move to {}a {},{}'.format(cnt, xx[1], yy[1])
#                    print 'wait for move complete'
#
#                if move_callback is not None:
#                    move_callback(xx[1], yy[1], 'slow')
#
# #                if n > 2 and not i * 2 >= n:
#                if i + 2 < n and not xs[i + 1] == xs[i + 2]:
#                    if verbose:
#                        print '===================== laser off'
#                    if end_callback is not None:
#                        end_callback()
#
#                    lasing = False
#                if use_plot:
#                    plot(xx, yy, 'r', linewidth=skip / 4.)
#                    text(xx[0], yy[0], '{}'.format(cnt))
#
#                cnt += 1
#                flip = True
#            else:
#                flip = False
#
#        if flip:
#            direction *= -1
#
#    if verbose:
#        print '===================== laser off'
#        print 'end raster'
#
#    if end_callback is not None:
#        end_callback()
#
#    if use_plot:
#        do_later(show)
# #        show()
