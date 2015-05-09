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
import math

from numpy import array, identity, sin, cos, radians
from scipy import linalg


class AffineTransform(object):
    '''
        affine transform 
        
        cumulative transform using augmented matrix A
        
    '''
    def __init__(self):
        self.A = array([[1, 0, 0],
                        [0, 1, 0],
                        [0, 0, 1]])
        self.A = identity(3)

    def translate(self, tx, ty):
        '''
           translation matrix
           T=[1 0 tx
              0 1 ty
              0 0 1]
        '''
        T = identity(3)
        T[0, 2] = tx
        T[1, 2] = ty
        self.A = self.A.dot(T)

    def rotate(self, theta):
        '''
            counter clockwise rotation
            
            rotation matrix
            R=[cos(t)  -si(t)  0
               sin(t)  cos(t)  0
               0       0       1] 
            
        '''
        theta = radians(theta)
        co = cos(theta)
        si = sin(theta)

        R = array([[co, -si, 0],
                   [si, co, 0],
                   [0, 0, 1]])
        self.A = self.A.dot(R)

    def scale(self, sx, sy):
        '''
            scale matrix 
            S= [sx  0  0
                0  sy  0
                0  0   1]
        '''
        S = identity(3)
        S[0, 0] = sx
        S[1, 1] = sy
        self.A = self.A.dot(S)

    def shear(self, hx, hy):
        '''
        shear matrix
        H=[1 hx 0
           hy 1 0
           0  0 1
            
        '''
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


'''
    Programming Computer Vision with Python:
    Tools and algorithms for analyzing images
'''
def calculate_rigid_transform(refpoints, points):
    '''
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
           
        return 
            s: scale
            theta: angle of rotation in degrees
            
            T: translation vector (tx,ty).  float tuple
            err: root mean square error 
             
    '''


    rows = []
    ys = []
    for (rx, ry), (x, y) in zip(refpoints, points):
        row = [x, -y, 1, 0]
        rows.append(row)
        row = [y, x, 0, 1]
        rows.append(row)
        ys.append([rx])
        ys.append([ry])

    A = array(rows)
    y = array(ys)
#    print A
#    print y
    soln = linalg.lstsq(A, y)
    print soln
    a, b, tx, ty = soln[0]
    tx = tx[0]
    ty = ty[0]
    sum_residuals = soln[1][0]

#    R = array([[a, -b], [b, a]])
    scale = (a ** 2 + b ** 2) ** 0.5
    theta = math.degrees(math.acos(a / scale))
    err = (sum_residuals / len(points)) ** 0.5 / float(scale)
    # print 'exception', err
#    print scale, float(scale)
    return float(scale), theta, map(float, (tx, ty)), err


import unittest
class RigidTransformTest(unittest.TestCase):
    def testtransfrom(self):
        dpt1, spt1 = (-5.933, -6.22), (-19686, 21622)
        dpt2, spt2 = (-4.604, -5.393), (-18026, 21886)
        dpt3, spt3 = (-4.604, -5.393), (-18026, 21885)

        dpt1, spt1 = (-1, 1), (-100, 100)
        dpt2, spt2 = (0, 1), (0, 100)
        dpt3, spt3 = (1, 1), (100, 100)

        dpt4, spt4 = (1, 0), (100, 0)
        dpt5, spt5 = (0, 0), (0, 0)
        dpt6, spt6 = (-1, 0), (-100, 0)

        dpt7, spt7 = (-1, -1), (-100, -100)
        dpt8, spt8 = (0, -1), (0, -100)
        dpt9, spt9 = (1, -1), (100, -101)


        refpoints = [spt1, spt2, spt3, spt4, spt5, spt6, spt7, spt8, spt9]
        points = [dpt1, dpt2, dpt3, dpt4, dpt5, dpt6, dpt7, dpt8, dpt9]
#        refpoints = list(map(lambda a: (a[0] / 10., a[1] / 10.), refpoints))
#        print points
        f, t, c, e = calculate_rigid_transform(refpoints, points)
        self.assertLess(e, 1e-10)


# ============= EOF ====================================
# import math
# class AffineTransform2:
#   "Represents a 2D + 1 affine transformation"
#   # use this for transforming points
#   # A = [ a c e]
#   #     [ b d f]
#   #     [ 0 0 1]
#   # self.A = [a b c d e f] = " [ A[0] A[1] A[2] A[3] A[4] A[5] ]"
#   def __init__(self, init=None):
#       if init:
#           if len(init) == 6 :
#               self.A = init
#           if type(init) == type(self):  # erpht!!! this seems so wrong
#               self.A = init.A
#       else:
#           self.A = [1.0, 0, 0, 1.0, 0.0, 0.0]  # set to identity
#
#   def scale(self, sx, sy):
#       self.A = [sx * self.A[0], sx * self.A[1], sy * self.A[2], sy * self.A[3], self.A[4], self.A[5] ]
#
#   def rotate(self, theta):
#       "counter clockwise rotation in standard SVG/libart coordinate system"
#       # clockwise in postscript "y-upward" coordinate system
#       # R = [ c  -s  0 ]
#       #     [ s   c  0 ]
#       #     [ 0   0  1 ]
#       co = math.cos(math.radians(theta))
#       si = math.sin(math.radians(theta))
#       self.A = [self.A[0] * co + self.A[2] * si,
#                 self.A[1] * co + self.A[3] * si,
#                 - self.A[0] * si + self.A[2] * co,
#                 - self.A[1] * si + self.A[3] * co,
#                 self.A[4],
#                 self.A[5] ]
#
#   def translate(self, tx, ty):
#       self.A = [ self.A[0], self.A[1], self.A[2], self.A[3],
#                   self.A[0] * tx + self.A[2] * ty + self.A[4],
#                   self.A[1] * tx + self.A[3] * ty + self.A[5] ]
#
#   def rightMultiply(self, a, b, c, d, e, f):
#       "multiply self.A by matrix M defined by coefficients a,b,c,d,e,f"
#       #
#
#       #             [    m0*a+m2*b,    m0*c+m2*d, m0*e+m2*f+m4]
#       #  ctm * M =  [    m1*a+m3*b,    m1*c+m3*d, m1*e+m3*f+m5]
#       #             [            0,            0,            1]
#       m = self.A
#       self.A = [ m[0] * a + m[2] * b,
#                  m[1] * a + m[3] * b,
#                  m[0] * c + m[2] * d,
#                  m[1] * c + m[3] * d,
#                  m[0] * e + m[2] * f + m[4],
#                  m[1] * e + m[3] * f + m[5] ]
#
#   #########  functions that act on points ##########
#
#   def transformPt(self, pt):
#       #                   [
#       #  pt = A * [x, y, 1]^T  =  [a*x + c*y+e, b*x+d*y+f, 1]^T
#       #
#       x, y = pt
#       a, b, c, d, e, f = self.A
#       return [ a * x + c * y + e, b * x + d * y + f]
#
#   def scaleRotateVector(self, v):
#       # scale a vector (translations are not done)
#       x, y = v
#       a, b, c, d, _e, _f = self.A
#       return [a * x + c * y, b * x + d * y]
#
#
#   def transformFlatList(self, seq):
#       # transform a (flattened) sequence of points in form [x0,y0, x1,y1,..., x(N-1), y(N-1)]
#       N = len(seq)  # assert N even
#
#       # would like to reshape the sequence, do w/ a loop for now
#       res = []
#       for ii in xrange(0, N, 2):
#           pt = self.transformPt((seq[ii], seq[ii + 1]))
#           res.extend(pt)
#
#       return res
#
# import unittest
# class AffineTest(unittest.TestCase):
#   def setUp(self):
#       self.standard_a = AffineTransform2()
#
#   def testNumpyAffineTransform(self):
#       tx, ty = 5, 5
#       px, py = 10, 6
#       theta = 5
#       xscale, yscale = 3, 5
#       self.standard_a.translate(tx, ty)
#       self.standard_a.rotate(theta)
#       self.standard_a.scale(xscale, yscale)
#       s = self.standard_a.transformPt((px, py))
#
#       af = AffineTransform()
#       af.translate(tx, ty)
#       af.rotate(theta)
#       af.scale(xscale, yscale)
#
#       n = af.transform(px, py)
#       self.assertEqual(tuple(s), n)
#        af.translate(theta)

