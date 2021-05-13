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
# from traits.api import Bool
# ============= standard library imports ========================
from numpy import zeros_like, invert, uint8, zeros, ones
# from skimage.filters import threshold_adaptive
# from skimage.feature import canny, peak_local_max
# from skimage.morphology import watershed
# from scipy import ndimage as ndi

# ============= local library imports  ==========================
from pychron.mv.segment.base import BaseSegmenter


class RegionSegmenter(BaseSegmenter):
    # use_adaptive_threshold = Bool(True)
    # blocksize = 20

    threshold_low = 0
    threshold_high = 255
    # use_watershed = Bool(True)

    def segment(self, image):
        """
        """
        # if self.use_adaptive_threshold:
        #     bs = self.blocksize
        #     if not bs % 2:
        #         bs += 1
        #
        #     markers = threshold_adaptive(image, bs)
        #     n = markers.astype('uint8')
        #     return n
        # else:
        nimage = zeros_like(image).astype('uint8')
        # print(self.threshold_high)
        # self.threshold_high = 150
        nimage[image >= self.threshold_high] = 255
        # distance = ndi.distance_transform_edt(nimage)
        # coords = peak_local_max(distance, footprint=ones((3, 3)), labels=nimage)
        # mask = zeros(distance.shape, dtype=bool)
        # mask[tuple(coords.T)] = True
        # markers, _ = ndi.label(mask)
        # labels = watershed(-distance, markers, mask=nimage)
        # print(labels)
        # labels[labels > 1] = 0
        return invert(nimage)
        # return labels.astype(uint8)
        # return invert(labels)
            # markers = zeros_like(image)
            # markers[image <= self.threshold_low] = 1
            # markers[image >= self.threshold_high] = 255

        # if self.use_watershed:
        #     elmap = canny(image, sigma=1)
        #     wsrc = watershed(elmap, markers, mask=image)
        #     return invert(wsrc.astype(uint8))
        # else:
        #     return invert(markers)

# ============= EOF =============================================
