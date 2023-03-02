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

# ============= enthought library imports =======================
from chaco.api import AbstractOverlay

# ============= standard library imports ========================
from numpy import linspace, hstack, sqrt, corrcoef, column_stack, array
from numpy.linalg import eig
from six.moves import zip
from traits.api import Bool, Enum

from pychron.pychron_constants import ELLIPSE_KINDS, ELLIPSE_KIND_SCALE_FACTORS


# ============= local library imports  ==========================
# http://www.earth-time.org/projects/upb/public_docs/ErrorEllipses.pdf
# 5) To create a 95% confidence ellipse from the 1s error ellipse, we must enlarge it by a factor of 2.4477.


def error_ellipse(sx, sy, pxy, kind, aspectratio=1):
    """
    return  a, b axes and rotation

    http://www.earth-time.org/projects/upb/public_docs/ErrorEllipses.pdf

    """
    covar = pxy * sx * sy
    covmat = [[sx * sx, covar], [covar, sy * sy]]
    w, v = eig(covmat)

    mi_w, ma_w = min(w), max(w)
    a = mi_w**0.5
    b = ma_w**0.5
    if sx > sy:
        b, a = a, b
    # else:
    #     a = mi_w ** 0.5
    #     b = ma_w ** 0.5
    sf = ELLIPSE_KIND_SCALE_FACTORS.get(kind, 1)
    a, b = a * sf, b * sf
    #        print aspectratio, dx, dy, width, height
    rotation = 0.5 * math.atan(1 / aspectratio * (2 * covar) / (sx**2 - sy**2))

    return a, b, rotation


class ErrorEllipseOverlay(AbstractOverlay):
    fill = Bool(True)
    kind = Enum(ELLIPSE_KINDS)

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        """ """
        gc.clip_to_rect(component.x, component.y, component.width, component.height)

        # x = component.index.get_data()
        # y = component.value.get_data()
        # xer = component.xerror.get_data()
        # yer = component.yerror.get_data()
        x = self.reg.xs
        y = self.reg.ys
        xer = self.reg.xserr
        yer = self.reg.yserr

        sel = component.index.metadata["selections"]

        pxy = array(self.reg.calculate_correlation_coefficients(clean=False))

        dx = abs(component.index_mapper.range.low - component.index_mapper.range.high)
        dy = abs(component.value_mapper.range.low - component.value_mapper.range.high)

        height = component.height
        width = component.width

        aspectratio = (dy / height) / (dx / width)

        try:
            for i, (cx, cy, sx, sy, pxyi) in enumerate(zip(x, y, xer, yer, pxy)):
                state = i not in sel
                a, b, rot = error_ellipse(
                    sx, sy, pxyi, self.kind, aspectratio=aspectratio
                )
                with gc:
                    self._draw_ellipse(gc, component, cx, cy, a, b, rot, state)

        except Exception as e:
            print("exception", e)

    def _draw_ellipse(self, gc, component, cx, cy, a, b, rot, state):
        if not state:
            gc.set_line_dash((5, 5))

        scx, scy = component.map_screen([(cx, cy)])[0]
        ox, oy = component.map_screen([(0, 0)])[0]

        x1 = linspace(-a, a, 200)
        y1 = b * sqrt((1 - (x1 / a) ** 2))

        x2 = x1[::-1]
        y2 = -b * sqrt((1 - (x2 / a) ** 2))

        x = hstack((x1, x2))
        y = hstack((y1, y2))
        pts = component.map_screen(column_stack((x, y)))

        gc.translate_ctm(scx, scy)

        gc.rotate_ctm(rot)
        gc.translate_ctm(-ox, -oy)

        gc.begin_path()
        gc.lines(pts)

        gc.set_stroke_color(self.border_color_)
        if self.fill:
            c = self.border_color_
            c = c[0], c[1], c[2], 0.5
            gc.set_fill_color(c)
            gc.draw_path()
        else:
            gc.stroke_path()


if __name__ == "__main__":
    x = [1, 2, 3, 4, 4.1]
    y = [1, 2, 3, 4, 5.5]
    xer = [0.1, 0.1, 0.1, 0.1, 0.1]
    yer = [0.1, 0.1, 0.1, 0.1, 0.1]

    ox = 0.1
    oy = 0.1

    pxy = corrcoef(x, y)[0][1]

    covar = ox * oy * pxy
    covmat = [[ox * ox, covar], [covar, oy * oy]]
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
    rotation = math.degrees(
        0.5 * math.atan(1 / aspectratio * (2 * covar) / (ox**2 - oy**2))
    )

#
# #        gc.begin_path()
# #        pts = component.map_screen(zip(x, ny))
#        gc.lines(pts)
#        gc.stroke_path()

#        gc.restore_state()
