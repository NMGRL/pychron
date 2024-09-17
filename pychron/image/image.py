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
from traits.api import HasTraits, Any, List, Int, Bool, Float

from numpy import asarray, flipud, ndarray, fliplr
from skimage.color import rgb2gray, gray2rgb
from skimage.transform import resize, rotate as trotate
from scipy.ndimage.interpolation import rotate as srotate


def fswap_rb(frame):
    red = frame[:, :, 2].copy()
    blue = frame[:, :, 0].copy()

    frame[:, :, 0] = red
    frame[:, :, 2] = blue


class Image(HasTraits):
    """ """

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
    rotate = Float(0)
    panel_size = Int(300)

    _cached_frame = None

    # @classmethod
    # def new_frame(cls, img, swap_rb=False):
    #     if isinstance(img, (str, unicode)):
    #         img = load_image(img, swap_rb)
    #
    #     elif isinstance(img, ndarray):
    #         img = asMat(asarray(img, dtype='uint8'))
    #         if swap_rb:
    #             img = cv_swap_rb(img)
    #
    #     return img
    #
    def load(self, img, swap_rb=False, nchannels=3):
        from cv2 import imread

        img = imread(img)
        if swap_rb:
            fswap_rb(img)
        self.source_frame = img

    def update_bounds(self, obj, name, old, new):
        if new:
            self.width = int(new[0])
            self.height = int(new[1])

    def _get_frame(self, **kw):
        return self.source_frame

    # def get_array(self, swap_rb=True, cropbounds=None):
    #     f = self.source_frame
    #     if swap_rb:
    #         f = self.source_frame.clone()
    #         f = cv_swap_rb(f)
    #
    #     a = f.as_numpy_array()
    #     if cropbounds:
    #         a = a[cropbounds[0]:cropbounds[1], cropbounds[2]:cropbounds[3]]
    #
    #     return flipud(a)  # [lx / 4:-lx / 4, ly / 4:-ly / 4]

    def get_frame(self, **kw):
        frame = self._get_frame(**kw)
        frame = self.modify_frame(frame, **kw)

        self._cached_frame = frame
        if frame is not None:
            if len(frame.shape) == 2:
                scalar = 255.0 / self.pixel_depth
                frame = gray2rgb(frame * scalar)

        #     self._cached_frame = frame
        # else:
        #     frame = self._cached_frame

        return frame

    def get_cached_frame(self, force=False):
        if self._cached_frame is None or force:
            self.get_frame()

        return self._cached_frame

    def get_image(self, **kw):
        frame = self.get_frame(**kw)
        return frame.to_pil_image()

    # def get_bitmap(self, **kw):  # flip = False, swap_rb = False, mirror = True):
    #     """
    #     """
    #     frame = self.get_frame(**kw)
    #     try:
    #         return frame.to_wx_bitmap()
    #     except AttributeError:
    #         pass

    def modify_frame(
        self,
        frame,
        vflip=None,
        hflip=None,
        gray=False,
        swap_rb=None,
        clone=False,
        rotate=None,
    ):
        if frame is not None:

            def _get_param(param, p):
                if param is None:
                    return getattr(self, p)
                else:
                    return param

            if clone:
                frame = frame.clone()

            if len(frame.shape) == 3:
                swap_rb = _get_param(swap_rb, "swap_rb")
                if swap_rb:
                    red = frame[:, :, 2].copy()
                    blue = frame[:, :, 0].copy()

                    frame[:, :, 0] = red
                    frame[:, :, 2] = blue

            if gray:
                frame = rgb2gray(frame)

            vflip = _get_param(vflip, "vflip")
            hflip = _get_param(hflip, "hflip")

            if vflip:
                frame = flipud(frame)
            if hflip:
                frame = fliplr(frame)

            rotate = _get_param(rotate, "rotate")
            if rotate:
                frame = srotate(frame, rotate)
                # frame = trotate(frame, rotate, preserve_range=True)

            return asarray(frame)

    def crop(self, src, ox, oy, cw, ch):
        h, w = src.shape[:2]

        x = int((w - cw) / 2.0 + ox)
        y = int((h - ch) / 2.0 + oy)
        try:
            return src[y : int(y + ch), x : int(x + cw)]
        except TypeError as e:
            print("crop", e)
            print("src", src)
            print("p", x, y, w, h, cw, ch)
            return

    def render(self):
        return self.frames[0]
        w = self.width
        h = self.height - 15
        try:
            return resize(self.frames[0], w, h, dst=(w, h, 3))
        except IndexError:
            pass

    # def save(self, path, src=None, swap=False):
    #     if src is None:
    #         src = self.render()
    #
    #     if swap:
    #         src = cv_swap_rb(src)
    #
    #     save_image(src, path)
    #
    # def _draw_crosshairs(self, src):
    #     r = 10
    #
    #     w, h = map(int, get_size(src))
    #     pts = [[(w / 2, 0), (w / 2, h / 2 - r)],
    #            [(w / 2, h / 2 + r), (w / 2, h)],
    #            [(0, h / 2), (w / 2 - r, h / 2)],
    #            [(w / 2 + r, h / 2), (w, h / 2)],
    #            ]
    #     draw_lines(src, pts, color=(0, 255, 255), thickness=1)


# ======== EOF ================================
