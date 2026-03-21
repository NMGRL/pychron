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
from scipy.ndimage import binary_fill_holes
from skimage.morphology import binary_closing

from pychron.mv.segment.base import BaseSegmenter


class RegionSegmenter(BaseSegmenter):
    def segment(self, image, threshold):
        """ """
        nimage = zeros_like(image, dtype="uint8")
        nimage[image >= threshold] = 255
        nimage = invert(nimage)
        nimage = binary_fill_holes(nimage).astype("uint8") * 255
        return nimage


# ============= EOF =============================================
