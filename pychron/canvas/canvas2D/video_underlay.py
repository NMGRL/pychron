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

# ============= enthought library imports =======================
from __future__ import absolute_import
from chaco.api import AbstractOverlay
from numpy import uint8, asarray
from skimage.color import gray2rgb
from skimage.transform import resize
from traits.api import Any


# ============= standard library imports ========================

# ============= local library imports  ==========================


class VideoUnderlay(AbstractOverlay):
    """
    video only needs to be an object the implements
    get_image_data([,size=(w,h)])
        returns  ndarray
    """

    video = Any
    _cached_image = None

    def overlay(self, component, gc, *args, **kw):
        """ """

        if self.video:
            with gc:
                img = self.video.get_image_data()
                if img is not None:
                    x, y, w, h = (
                        component.x,
                        component.y,
                        component.width,
                        component.height,
                    )
                    gc.clip_to_rect(x, y, w, h)
                    gc.translate_ctm(x, y)
                    try:
                        gc.draw_image(
                            asarray(
                                resize(img, (int(h), int(w)), preserve_range=True),
                                dtype=uint8,
                            )
                        )
                    except (IndexError, ValueError):
                        pass


# ============= EOF ====================================
