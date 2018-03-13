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
from __future__ import absolute_import
from traits.api import Bool
# ============= standard library imports ========================
from numpy import zeros_like, invert
from skimage.filters import threshold_adaptive
from skimage.feature import canny
from skimage.morphology import watershed
# ============= local library imports  ==========================
from pychron.mv.segment.base import BaseSegmenter


class RegionSegmenter(BaseSegmenter):
    use_adaptive_threshold = Bool(True)
    threshold_low = 0
    threshold_high = 255
    blocksize = 20

    def segment(self, image):
        """
        """
        # image = src[:]
        if self.use_adaptive_threshold:
            bs = self.blocksize
            if not bs % 2:
                bs += 1

            markers = threshold_adaptive(image, bs)

            # n = markers[:].astype('uint8')
            n = markers.astype('uint8')
            # n[markers] = 255
            # n[invert(markers)] = 1
            # markers = n
            return n
        else:
            markers = zeros_like(image)
            # print('image',image.max(), image.min())
            # print('le', image<self.threshold_low)
            # print('ge', image>self.threshold_high)
            markers[image <= self.threshold_low] = 1
            markers[image > self.threshold_high] = 255

        #elmap = sobel(image, mask=image)
        elmap = canny(image, sigma=1)
        wsrc = watershed(elmap, markers, mask=image)

        return invert(wsrc)

# ============= EOF =============================================
