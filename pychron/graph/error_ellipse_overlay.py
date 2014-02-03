#===============================================================================
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
#===============================================================================



#============= enthought library imports =======================
from chaco.api import AbstractOverlay
from traits.api import Bool
#============= standard library imports ========================
from numpy import linspace, hstack, sqrt, power, corrcoef, column_stack, array, delete
from numpy.linalg import eig
import math

#============= local library imports  ==========================

# http://www.earth-time.org/projects/upb/public_docs/ErrorEllipses.pdf
# 5) To create a 95% confidence ellipse from the 1s error ellipse, we must enlarge it by a factor of 2.4477.

SCALE_FACTOR = 2.4477


def error_ellipse(sx, sy, pxy, aspectratio=1):
    """
        return  a, b axes and rotation

        http://www.earth-time.org/projects/upb/public_docs/ErrorEllipses.pdf

    """
    covar = pxy * sx * sy
    covmat = [[sx * sx, covar],
              [covar, sy * sy]]
    w, v = eig(covmat)

    #print v
    mi_w, ma_w = min(w), max(w)
    #print sx, sy, sx>sy
    if sx > sy:
        a = ma_w ** 0.5
        b = mi_w ** 0.5
    else:
        a = mi_w ** 0.5
        b = ma_w ** 0.5

    a, b = a * SCALE_FACTOR, b * SCALE_FACTOR
    #        print aspectratio, dx, dy, width, height
    rotation = 0.5 * math.atan(1 / aspectratio * (2 * covar) / (sx ** 2 - sy ** 2))

    return a, b, rotation


class ErrorEllipseOverlay(AbstractOverlay):
    fill=Bool(True)

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        """

        """
        #        gc.save_state()
        gc.clip_to_rect(component.x, component.y, component.width, component.height)

        x = component.index.get_data()
        y = component.value.get_data()
        xer = component.xerror.get_data()
        yer = component.yerror.get_data()

        sel=component.index.metadata['selections']

        x=delete(x, sel)
        y=delete(y, sel)
        xer=delete(xer, sel)
        yer=delete(yer, sel)
        pxy=array(self.reg._calculate_correlation_coefficients())

        dx = abs(component.index_mapper.range.low -
                 component.index_mapper.range.high)
        dy = abs(component.value_mapper.range.low -
                 component.value_mapper.range.high)

        height = component.height
        width = component.width

        aspectratio = (dy / height) / (dx / width)
        # aspectratio=(height/width)
        # aspectratio=(dy/dx)
        # aspectratio=self.component.aspect_ratio
        aspectratio=1
        try:
            for cx, cy, sx, sy, pxyi in zip(x, y, xer, yer, pxy):
                a, b, rot = error_ellipse(sx, sy, pxyi, aspectratio=aspectratio)
                #print a,b,rot
                #a, b, rot = self.calculate_ellipse(component, cx, cy, ox, oy, pxy)
                #gc.save_state()
                with gc:
                    self._draw_ellipse(gc, component, cx, cy, a, b, rot)
                    #gc.restore_state()
        except Exception, e:
            print e

    def _draw_ellipse(self, gc, component, cx, cy, a, b, rot):
        #a *= self.nsigma
        #b *= self.nsigma
        scx, scy = component.map_screen([(cx, cy)])[0]
        ox, oy = component.map_screen([(0, 0)])[0]

        #        gc.translate_ctm(-scx, -scy)
        # gc.rotate_ctm(45)
        x1 = linspace(-a, a, 200)
        y1 = b * sqrt((1 - power(x1 / a, 2)))

        x2 = x1[::-1]
        y2 = -b * sqrt((1 - power(x2 / a, 2)))

        x = hstack((x1, x2))
        y = hstack((y1, y2))
        pts = component.map_screen(column_stack((x, y)))

        gc.translate_ctm(scx, scy)

        gc.rotate_ctm(rot)
        # gc.rotate_ctm(rot-math.pi/2.0)
        gc.translate_ctm(-ox, -oy)
        #gc.translate_ctm(-scx, -scy)

        #gc.translate_ctm(scx - ox, scy - oy)

        gc.begin_path()
        gc.lines(pts)
        if self.fill:
            gc.set_fill_color((0,0,0,0.5))
            gc.fill_path()
        else:
            gc.stroke_path()


if __name__ == '__main__':
    x = [1, 2, 3, 4, 4.1]
    y = [1, 2, 3, 4, 5.5]
    xer = [0.1, 0.1, 0.1, 0.1, 0.1]
    yer = [0.1, 0.1, 0.1, 0.1, 0.1]

    ox = 0.1
    oy = 0.1

    pxy = corrcoef(x, y)[0][1]

    covar = ox * oy * pxy
    covmat = [[ox * ox, covar],
              [covar, oy * oy]]
    w, _v = eig(covmat)

    if ox > oy:
        a = (max(w)) ** 0.5
        b = (min(w)) ** 0.5
    else:
        a = (min(w)) ** 0.5
        b = (max(w)) ** 0.5

    dx = 1
    dy = 1
    height = 1
    width = 1
    aspectratio = (dy / height) / (dx / width)
    rotation = math.degrees(0.5 * math.atan(1 / aspectratio * (2 * covar) / (ox ** 2 - oy ** 2)))


#
# #        gc.begin_path()
# #        pts = component.map_screen(zip(x, ny))
#        gc.lines(pts)
#        gc.stroke_path()

#        gc.restore_state()
