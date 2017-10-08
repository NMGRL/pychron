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
import math

from numpy import array, identity, sin, cos, radians
from scipy import linalg


class AffineTransform(object):
    """
        affine transform

        cumulative transform using augmented matrix A

    """

    def __init__(self):
        self.A = identity(3)

    def translate(self, tx, ty):
        """
           translation matrix
           T=[1 0 tx
              0 1 ty
              0 0 1]
        """
        T = identity(3)
        T[0, 2] = tx
        T[1, 2] = ty
        self.A = self.A.dot(T)

    def rotate(self, theta):
        """
            counter clockwise rotation

            rotation matrix
            R=[cos(t)  -sin(t)  0
               sin(t)  cos(t)  0
               0       0       1]

        """
        theta = radians(theta)
        co = cos(theta)
        si = sin(theta)

        R = array([[co, -si, 0],
                   [si, co, 0],
                   [0, 0, 1]])
        self.A = self.A.dot(R)

    def scale(self, sx, sy):
        """
            scale matrix
            S= [sx  0  0
                0  sy  0
                0  0   1]
        """
        S = identity(3)
        S[0, 0] = sx
        S[1, 1] = sy
        self.A = self.A.dot(S)

    def shear(self, hx, hy):
        """
        shear matrix
        H=[1 hx 0
           hy 1 0
           0  0 1

        """
        H = identity(3)
        H[0, 1] = hx
        H[1, 0] = hy
        self.A = self.A.dot(H)

    def transform(self, px, py):
        v = self.new_vector(px, py)
        T = self.A.dot(v)
        return T[0, 0], T[1, 0]

    def new_vector(self, x, y):
        return array([[x], [y], [1]])


def transform_point(pos, cpos, rot, scale):
    a = AffineTransform()
    a.scale(scale, scale)
    a.translate(cpos[0], cpos[1])
    a.rotate(rot)

    pos = a.transform(*pos)
    return pos


def itransform_point(pos, cpos, rot, scale):
    a = AffineTransform()
    a.scale(1 / scale, 1 / scale)
    a.rotate(-rot)
    a.translate(-cpos[0], -cpos[1])

    pos = a.transform(*pos)
    return pos


'''
    Programming Computer Vision with Python:
    Tools and algorithms for analyzing images
'''


def calculate_rigid_itransform_affine(refpoints, datapoints):
    """
    used to map a pt in refpoint space to points space

    returns an AffineTransform object.

    use x,y = af.transform(sx,sy)
    where sx,sy is in refs space

    @param refpoints: list of 2-tuples
    @param datapoints: list of 2-tuples
    @return: AffineTransform
    """
    t, scale, err = calc_transform_matrix(refpoints, datapoints)
    r = linalg.inv(t)
    af = AffineTransform()
    af.A = r
    return af


def calculate_rigid_itransform(refpoints, datapoints):
    return calc_transform_parameters(refpoints, datapoints, invert=True)


def calculate_rigid_transform(refpoints, points):
    return calc_transform_parameters(refpoints, points)


def calc_transform_parameters(refpoints, datapoints, invert=False):
    """
    return  scale, theta, tx,ty, err
    s: scale
    theta: angle of rotation in degrees
    tx,ty = translation vector
    err: root mean square error

    @param refpoints:
    @param datapoints:
    @param invert:
    @return:
    """
    t, scale, err = calc_transform_matrix(refpoints, datapoints)
    if invert:
        r = linalg.inv(t)

    a, b = r[0, 0], -r[0, 1]
    tx, ty = r[0, 2], r[1, 2]

    theta = math.degrees(math.acos(a / scale))
    if invert:
        theta = -theta

    return scale, theta, tx, ty, err


def calc_transform_matrix(refpoints, datapoints):
    soln = solve_matrix(refpoints, datapoints)
    a, b, tx, ty = soln[0]

    sum_residuals = soln[1]
    scale = (a ** 2 + b ** 2) ** 0.5
    err = (sum_residuals / len(datapoints)) ** 0.5 / scale
    return array([[a, -b, tx],
                  [b, a, ty],
                  [0, 0, 1]]), scale, err


def solve_matrix(refpoints, datapoints):
    """
        A=[[x1 -y1  1 0]
           [y1  x1  0 1]
           [x2 -y2  1 0]
           ...
           [yn  xn  0 1]]

        y=[[x1]
           [y1]
           [x2]
           [y2]
           ...
           [xn]
           [yn]
           ]

    """
    ys = [a for args in refpoints
          for a in args]
    rows = [row for x, y in datapoints
            for row in ((x, -y, 1, 0), (y, x, 0, 1))]

    big_a = array(rows)
    y = array(ys)
    return linalg.lstsq(big_a, y)

# ============= EOF ====================================
# import unittest
#
#
# class RigidTransformTest(unittest.TestCase):
#     def testtransfrom(self):
#         dpt1, spt1 = (-5.933, -6.22), (-19686, 21622)
#         dpt2, spt2 = (-4.604, -5.393), (-18026, 21886)
#         dpt3, spt3 = (-4.604, -5.393), (-18026, 21885)
#
#         dpt1, spt1 = (-1, 1), (-100, 100)
#         dpt2, spt2 = (0, 1), (0, 100)
#         dpt3, spt3 = (1, 1), (100, 100)
#
#         dpt4, spt4 = (1, 0), (100, 0)
#         dpt5, spt5 = (0, 0), (0, 0)
#         dpt6, spt6 = (-1, 0), (-100, 0)
#
#         dpt7, spt7 = (-1, -1), (-100, -100)
#         dpt8, spt8 = (0, -1), (0, -100)
#         dpt9, spt9 = (1, -1), (100, -101)
#
#         refpoints = [spt1, spt2, spt3, spt4, spt5, spt6, spt7, spt8, spt9]
#         points = [dpt1, dpt2, dpt3, dpt4, dpt5, dpt6, dpt7, dpt8, dpt9]
#         # refpoints = list(map(lambda a: (a[0] / 10., a[1] / 10.), refpoints))
#         # print points
#         f, t, c, e = calculate_rigid_transform(refpoints, points)
#         # self.assertLess(e, 1e-10)
#         self.assertEqual(f, 100)
