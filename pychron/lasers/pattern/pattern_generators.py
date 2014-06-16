# ===============================================================================
# Copyright 2011 Jake Ross
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

#============= enthought library imports =======================

#============= standard library imports ========================
import math
import random

from numpy import linspace, cos, sin, hstack

#============= local library imports  ==========================
from pychron.core.geometry.affine import AffineTransform


def trough_pattern(cx, cy, length, width, rotation, use_x):
    """
    1 -------------- 2
    |                |
    4 -------------- 3
    """
    p1 = (cx, cy)
    p2 = (cx + length, cy)
    p3 = (cx + length, cy - width)
    p4 = (cx, cy - width)

    a = AffineTransform()
    a.translate(-cx, cy)
    a.rotate(rotation)
    a.translate(cx, cy)

    if use_x:
        ps = (p1, p2, p4, p3, p1)
    else:
        ps = (p1, p2, p3, p4, p1)

    for p in ps:
        yield a.transform(*p)


def line_pattern(cx, cy, length, rotation, n):
    p1 = (cx, cy)
    p2 = (cx + length, cy)

    for i in xrange(n):
        a = AffineTransform()
        a.translate(-cx, cy)
        a.rotate(rotation)
        a.translate(cx, cy)
        if i % 2 == 0:
            ps = (p1, p2)

        else:
            ps = (p2, p1)

        for x, y in ps:
            yield a.transform(x, y)


def circular_contour_pattern(cx, cy, radius, nsteps, pc):
    for ni in range(nsteps):
        ps = [pi for pi in arc_pattern(cx, cy, 360, radius * (1 + ni * pc))][1:-1]
        for pi in ps:
            yield pi


def polygon_pattern(cx, cy, radius, nsides, rotation=0):
    for i in range(nsides + 1):
        #        if i == 0: #or i == nsides + 2:
        #            x, y = cx, cy
        #        else:
        a = 360 * i / float(nsides) + rotation
        x = cx + radius * math.cos(math.radians(a))
        y = cy + radius * math.sin(math.radians(a))
        yield x, y


def arc_pattern(cx, cy, degrees, radius):
    '''
         only used for drawing
    '''

    x = radius * cos(map(math.radians, linspace(0, degrees, degrees / 10.0))) + cx
    y = radius * sin(map(math.radians, linspace(0, degrees, degrees / 10.0))) + cy

    xs = hstack(([cx], x))
    xs = hstack((xs, [cx]))

    ys = hstack(([cy], y))
    ys = hstack((ys, [cy]))

    for pt in zip(xs, ys):
        yield pt


def random_pattern(cx, cy, walk_x, walk_y, ns, shape='circle', **kw):
    '''
        this method generates a more even distribution around the center than 
        method 1.
        
        method 1.
        ra = math.radians(random.random()*360)
        x = cx + walk_x * random.random()*math.cos(ra)
        y = cx + walk_y * random.random()*math.sin(ra)
        
        method 2. preferred
        generate random x and y point in square centered on cx, cy
        if shape is circle check if displacement of point from center is greater than radius
        
        
    '''

    for _ni in range(ns):
        # gen random point in a square

        while 1:
            x = cx + (random.random() * 2 - 1) * walk_x
            y = cy + (random.random() * 2 - 1) * walk_y

            # check if in circle
            disp = math.sqrt((cx - x) ** 2 + (cy - y) ** 2)
            if disp <= walk_x or shape != 'circle':
                break

        yield x, y


def diamond_pattern(cx, cy, width, height, **kw):
    '''
         2
        
     3   0,6   1,5
         
         4
    
    @deprecated: use polygon pattern instead 
         
    '''
    half_width = width / 2.0
    half_height = height / 2.0
    pts = [(cx + half_width, cy),
           (cx, cy + half_height),
           (cx - half_width, cy),
           (cx, cy - half_height),
           (cx + half_width, cy),
           (cx, cy)
    ]
    for pt in pts:
        yield pt


def square_spiral_pattern(cx, cy, R, ns, p, direction='out', ox=None, oy=None, **kw):
    '''
        cx,cy= center point to spiral around
        R = nominal spiral diameter
        ns= number of spirals
        p= percent change in radius of spiral
    '''

    rfunc = lambda i: R * (1 + (i) * p)
    ns = 4 * ns + 1
    steps = xrange(ns)
    funclist = [lambda x, y, r: (x + r, y),
                lambda x, y, r: (x, y + r),
                lambda x, y, r: (x - r, y),
                lambda x, y, r: (x, y - r)]

    if direction == 'in':
        rfunc = lambda i: R * (1 + (ns - i) * p)
        funclist = funclist[1:] + funclist[:1]

    x = cx
    y = cy
    if ox is not None and oy is not None:
        x = ox
        y = oy

    for i in steps:
        r = rfunc(i)
        if direction == 'in' and i == 0:
            yield x, y

        func = funclist[i % 4]

        x, y = func(x, y, r)

        yield x, y


def line_spiral_pattern(cx, cy, R, ns, p, ss, direction='out', **kw):
    '''
        cx,cy= center point to spiral around
        R = nominal spiral
        ns= number of spirals
        p= percent change in radius of spiral
        ss= step scalar ie min number of steps per rotation
    '''
    stepfunc = lambda i: 2 * i + ss
    rfunc = lambda i, j: R * (1 + (i + j / 360.) * p)
    if direction == 'in':
        stepfunc = lambda i: 2 * (ns - i) + ss
        rfunc = lambda i, j: R * (1 + ((ns - i - 1) + (360 - j) / 360.) * p)

    for ni in xrange(ns):
        nstep = stepfunc(ni)
        for t in linspace(0, 360, nstep):
            if t == 360 and ni != ns - 1:
                continue

            r = rfunc(ni, t)
            theta = math.radians(t)
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)

            yield x, y

#============= EOF ====================================


