# ===============================================================================
# Copyright 2013 Jake Ross
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
from numpy import invert, zeros_like, asarray
from skimage.draw import circle


# ============= local library imports  ==========================

def area(a):
    b = asarray(a, dtype=bool)
    return b.sum()


class LumenDetector(object):
    threshold = 25
    pxpermm = 23

    mask_kind = 'Hole'
    beam_radius = 0
    custom_mask_radius = 0
    hole_radius = 0


    def get_value(self, src, scaled=True):
        """

        if scaled is True
        return sum of all pixels in masked area / (masked area *255)

        @param src:
        @param scaled:
        @return:
        """

        mask = self._mask(src)
        self._preprocess(src)

        lum = src[mask]

        v = lum.sum()

        if scaled:
            v /= (mask.sum() * 255.)
        # print lum.sum(), v
        return src, v

    def get_scores(self, src):
        mask = self._mask(src)
        self._preprocess(src)

        lum = src[mask]

        v = lum.sum()
        try:
            score_density = v / area(lum)
        except ZeroDivisionError:
            score_density = 0

        score_saturation = v / (mask.sum() * 255.)

        return score_density, score_saturation, lum

    def _mask(self, src):
        radius = self.mask_radius

        h, w = src.shape[:2]
        c = circle(h / 2., w / 2., radius)
        mask = zeros_like(src, dtype=bool)
        mask[c] = True
        src[invert(mask)] = 0
        return mask

    def _preprocess(self, src):
        threshold = self.threshold
        src[src < threshold] = 0

    @property
    def mask_radius(self):
        if self.mask_kind == 'Hole':
            d = self.hole_radius
        elif self.mask_kind == 'Beam':
            d = max(0.1, self.beam_radius * 1.1)
        else:
            d = self.custom_mask_radius

        return d * self.pxpermm

# ============= EOF =============================================
