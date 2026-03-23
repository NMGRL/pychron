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
import time

from chaco.api import AbstractOverlay
from numpy import uint8, asarray
from skimage.color import gray2rgb
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
    _cached_bounds = None
    _last_refresh = 0

    def __init__(self, *args, **kw):
        super(VideoUnderlay, self).__init__(*args, **kw)
        self.offset = (0, 0)

    def overlay(self, component, gc, *args, **kw):
        """ """

        if self.video:
            with gc:
                x, y, w, h = (
                    component.x,
                    component.y,
                    component.width,
                    component.height,
                )
                img = self._get_cached_image(component, int(w), int(h))
                if img is not None:
                    gc.clip_to_rect(x, y, w, h)
                    gc.translate_ctm(x, y)
                    gc.translate_ctm(*self.offset)
                    gc.draw_image(img, rect=(0, 0, w, h))

    def request_refresh(self):
        self._last_refresh = 0
        self._cached_image = None
        self._cached_bounds = None

    def _get_cached_image(self, component, width, height):
        now = time.time()
        bounds = (width, height)
        if (
            self._cached_image is not None
            and self._cached_bounds == bounds
            and now - self._last_refresh < self._frame_interval(component)
        ):
            return self._cached_image

        img = self._get_image_data(width, height)
        if img is None:
            return self._cached_image

        prepared = self._prepare_image(img)
        if prepared is not None:
            self._cached_image = prepared
            self._cached_bounds = bounds
            self._last_refresh = now

        return self._cached_image

    def _get_image_data(self, width, height):
        try:
            return self.video.get_image_data(size=(height, width))
        except TypeError:
            return self.video.get_image_data()

    def _prepare_image(self, img):
        try:
            if len(img.shape) == 2:
                img = gray2rgb(img)
            elif len(img.shape) != 3:
                return

            if not img.flags["C_CONTIGUOUS"]:
                img = img.copy()

            if img.dtype != uint8:
                img = asarray(img, dtype=uint8)

            return img
        except (AttributeError, IndexError, ValueError):
            return

    def _frame_interval(self, component):
        fps = getattr(component, "fps", 0) or getattr(self.video, "fps", 0) or 0
        if fps <= 0:
            return 0

        return 1.0 / float(fps)


# ============= EOF ====================================
