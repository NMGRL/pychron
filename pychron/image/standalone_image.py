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
from __future__ import absolute_import
from traits.api import Array, Event, Range, Bool
from traitsui.api import UItem, Item, VGroup

# ============= standard library imports ========================
from numpy import asarray, array, ndarray, hstack, resize, zeros, reshape, ones
from PIL import Image

# ============= local library imports  ==========================
from pychron.image.cv_wrapper import colorspace, grayspace
from pychron.options.layout import filled_grid
from pychron.viewable import Viewable
from pychron.core.ui.image_editor import ImageEditor


class FrameImage(Viewable):
    source_frame = Array
    refresh_needed = Event
    alpha = Range(0.0, 1.0)
    overlays = None
    alpha_enabled = Bool(True)
    osource_frame = None
    tiles = None

    def clear(self):
        self.tiles = []
        self.osource_frame = None

    def load(self, frame, swap_rb=False):
        self.source_frame = array(frame)
        self.refresh_needed = True

    def tile(self, frame):
        if not self.tiles:
            self.tiles = []

        self.tiles.append(colorspace(frame))

    def tilify(self):
        if self.osource_frame is None:
            self.osource_frame = self.source_frame[:]
            # self.osource_frame = reshape(self.osource_frame, (1000, 1000, 3))

        r, c = filled_grid(len(self.tiles) + 1)
        r += 1
        c += 1
        th, tw, _ = self.osource_frame.shape
        nf = ones((th * r, tw * c, 3))
        nf[:] = (100, 100, 100)
        h, w, _ = self.osource_frame.shape
        nf[0:h, 0:w] = self.osource_frame
        starth, endh, startw, endw = 0, h, w + 5, 2 * w
        for i, t in enumerate(self.tiles):
            if startw + w >= tw * c:
                startw = 0
                starth += h + 5

            nf[starth:starth + h, startw:startw + w] = t
            startw += w + 5

        self.source_frame = colorspace(nf)

    def set_frame(self, frame):
        if not isinstance(frame, ndarray):
            frame = asarray(frame)

        self.overlays = None
        self.source_frame = frame
        self.refresh_needed = True

    def overlay(self, frame, alpha):
        im0 = Image.fromarray(self.source_frame)
        im1 = Image.fromarray(frame)

        self.overlays = (im0, im1)

        o = self.alpha
        self.alpha = alpha
        if alpha == o:
            self._alpha_changed()

    def _overlay(self, im0, im1, alpha):
        try:
            arr = Image.blend(im1, im0, alpha)
            self.source_frame = asarray(arr)
            self.refresh_needed = True
        except ValueError:
            pass

    def _alpha_changed(self):
        if self.overlays:
            im0, im1 = self.overlays
            self._overlay(im0, im1, self.alpha)


class StandAloneImage(FrameImage):
    def traits_view(self):
        img = UItem("source_frame", editor=ImageEditor(refresh="refresh"))
        if self.alpha_enabled:
            vv = VGroup(Item("alpha"), img)
        else:
            vv = img
        v = self.view_factory(VGroup(vv))
        return v

# ============= EOF =============================================
