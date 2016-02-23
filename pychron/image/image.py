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

# =============enthought library imports=======================
from traits.api import HasTraits, Any, List, Int, Bool
# =============standard library imports ========================
from numpy import asarray, flipud, ndarray
# =============local library imports  ==========================
from cv_wrapper import load_image, asMat, get_size, grayspace, resize, \
    save_image, draw_lines
from cv_wrapper import swap_rb as cv_swap_rb
from cv_wrapper import flip as cv_flip
from pychron.globals import globalv


class Image(HasTraits):
    """
    """
    frames = List
    source_frame = Any
    width = Int
    height = Int
    _bitmap = None
    _frame = None

    graphics_container = None

    swap_rb = Bool(False)
    hflip = Bool(False)
    vflip = Bool(False)
    panel_size = Int(300)

    _cached_frame = None

    @classmethod
    def new_frame(cls, img, swap_rb=False):
        if isinstance(img, (str, unicode)):
            img = load_image(img, swap_rb)

        elif isinstance(img, ndarray):
            img = asMat(asarray(img, dtype='uint8'))
            if swap_rb:
                img = cv_swap_rb(img)

        return img

    def load(self, img, swap_rb=False, nchannels=3):

        img = self.new_frame(img, swap_rb)
        self.source_frame = img

    def update_bounds(self, obj, name, old, new):
        if new:
            self.width = int(new[0])
            self.height = int(new[1])

    def _get_frame(self, **kw):
        return self.source_frame

    def get_array(self, swap_rb=True, cropbounds=None):
        f = self.source_frame
        if swap_rb:
            f = self.source_frame.clone()
            f = cv_swap_rb(f)

        a = f.as_numpy_array()
        if cropbounds:
            a = a[cropbounds[0]:cropbounds[1], cropbounds[2]:cropbounds[3]]

        return flipud(a)  # [lx / 4:-lx / 4, ly / 4:-ly / 4]

    def get_frame(self, **kw):
        frame = self._get_frame(**kw)
        frame = self.modify_frame(frame, **kw)
        self._cached_frame = frame
        return frame

    def get_cached_frame(self):
        if self._cached_frame is None:
            self.get_frame()

        return self._cached_frame

    def get_image(self, **kw):
        frame = self.get_frame(**kw)
        return frame.to_pil_image()

    def get_bitmap(self, **kw):  # flip = False, swap_rb = False, mirror = True):
        """
        """
        frame = self.get_frame(**kw)
        try:
            return frame.to_wx_bitmap()
        except AttributeError:
            pass

    def modify_frame(self, frame, vflip=None, hflip=None, gray=False, swap_rb=None,
                     clone=False, croprect=None, size=None):
        if frame is not None:
            def _get_param(param, p):
                if param is None:
                    return getattr(self, p)
                else:
                    return param

            swap_rb = _get_param(swap_rb, 'swap_rb')
            vflip = _get_param(vflip, 'vflip')
            hflip = _get_param(hflip, 'hflip')

            if clone:
                frame = frame.clone()

            if swap_rb:
                frame = cv_swap_rb(frame)

            if gray:
                frame = grayspace(frame)

            if croprect:
                if len(croprect) == 2:  # assume w, h
                    w, h = get_size(frame)
                    croprect = (w - croprect[0]) / 2, (h - croprect[1]) / 2, croprect[0], croprect[1]
                else:
                    pass

                rs = croprect[0]
                re = croprect[0] + croprect[2]
                cs = croprect[1]
                ce = croprect[1] + croprect[3]

                frame = asMat(frame.ndarray[cs:ce, rs:re])

            if size:
                frame = resize(frame, *size)

            if not globalv.video_test:
                if vflip:
                    if hflip:
                        cv_flip(frame, -1)
                    else:
                        cv_flip(frame, 0)
                elif hflip:
                    cv_flip(frame, 1)

        return frame

    def crop(self, src, ox, oy, cw, ch):
        h, w = src.shape[:2]

        x = int((w - cw) / 2. + ox)
        y = int((h - ch) / 2. + oy)

        return src[y:y + ch, x:x + cw]

    def render(self):
        return self.frames[0]
        w = self.width
        h = self.height - 15
        try:
            return resize(self.frames[0], w, h, dst=(w, h, 3))
        except IndexError:
            pass

    def save(self, path, src=None):
        if src is None:
            src = self.render()
        save_image(src, path)

    def _draw_crosshairs(self, src):
        r = 10

        w, h = map(int, get_size(src))
        pts = [[(w / 2, 0), (w / 2, h / 2 - r)],
               [(w / 2, h / 2 + r), (w / 2, h)],
               [(0, h / 2), (w / 2 - r, h / 2)],
               [(w / 2 + r, h / 2), (w, h / 2)],
               ]
        draw_lines(src, pts, color=(0, 255, 255), thickness=1)

# ======== EOF ================================
