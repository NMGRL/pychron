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
from traits.api import Bool
# ============= standard library imports ========================
from numpy import zeros_like, invert
from skimage.filter import threshold_adaptive, canny
from skimage.morphology import watershed
# ============= local library imports  ==========================
from pychron.mv.segment.base import BaseSegmenter


cnt = 0


class RegionSegmenter(BaseSegmenter):
    use_adaptive_threshold = Bool(True)
    threshold_low = 0
    threshold_high = 255
    block_size = 20

    def segment(self, image):
        """
            pychron: preprocessing cv.Mat
        """
        # image = src[:]
        if self.use_adaptive_threshold:
            markers = threshold_adaptive(image, self.block_size)

            # n = markers[:].astype('uint8')
            n = markers.astype('uint8')
            n[markers] = 255
            n[not markers] = 1
            markers = n

        else:
            markers = zeros_like(image)
            markers[image < self.threshold_low] = 1
            markers[image > self.threshold_high] = 255

        # elmap = sobel(image, mask=image)
        elmap = canny(image, sigma=3)
        wsrc = watershed(elmap, markers, mask=image)

        return invert(wsrc)

# ============= EOF =============================================
