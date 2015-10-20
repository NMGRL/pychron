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
# ============= local library imports  ==========================
from numpy import invert, zeros_like
from skimage.draw import circle


class LumenDetector(object):
    threshold = 100
    mask_radius = 70

    def get_value(self, src):
        mask = self._mask(src)
        self._preprocess(src)

        lum = src[mask]
#         # use mean of the 90th percentile as lumen
#         # measure. this is adhoc and should/could be modified
        #         lumen = percentile(lum.flatten(), 90).mean()
        lumen = lum.sum()
        return src, lumen

    def _mask(self, src):
        radius = self.mask_radius
        h, w = src.shape
        c = circle(h / 2., w / 2., radius)
        mask = zeros_like(src, dtype=bool)
        mask[c] = True
        src[invert(mask)] = 0
        return mask

    def _preprocess(self, src):
        threshold = self.threshold
        src[src < threshold] = 0


# ============= EOF =============================================
