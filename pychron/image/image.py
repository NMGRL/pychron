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
# import wx
from numpy import asarray, flipud, ndarray
from pychron.globals import globalv
# from pychron.image.pyopencv_image_helper import colorspace
# =============local library imports  ==========================
from cv_wrapper import load_image, asMat, get_size, grayspace, resize, \
    save_image, draw_lines
from cv_wrapper import swap_rb as cv_swap_rb
from cv_wrapper import flip as cv_flip

# try:
#    from cvwrapper import swapRB, grayspace, cvFlip, \
#    draw_lines, new_dst, \
#    resize, asMat, save_image, load_image, \
#    get_size, cv_swap_rb
# except ImportError:
#    pass
# class GraphicsContainer(object):
#
#    _lines = None
#
#    def add_line(self, l):
#        if self._lines is None:
#            self._lines = [l]
#        else:
#            self._lines.append(l)
#
#    @property
#    def lines(self):
#        return self._lines
# from numpy.core.numeric import zeros
# import Image as PILImage

# from pychron.core.helpers.memo import memoized
class Image(HasTraits):
    '''
    '''
    frames = List
    source_frame = Any
#    current_frame = Any
    width = Int
    height = Int
    _bitmap = None
    _frame = None

    graphics_container = None

    swap_rb = Bool(False)
    hflip = Bool(False)
    vflip = Bool(False)
#    mirror = Bool(False)
    panel_size = Int(300)

    @classmethod
    def new_frame(cls, img, swap_rb=False):
        if isinstance(img, (str, unicode)):
            img = load_image(img, swap_rb)

        elif isinstance(img, ndarray):
            img = asMat(asarray(img, dtype='uint8'))

        if swap_rb:
            cv_swap_rb(img)

        return img

    def load(self, img, swap_rb=False, nchannels=3):
#        if isinstance(img, (str, unicode)):
#            img = load_image(img, swap_rb)
#
#        elif isinstance(img, ndarray):
#            img = asMat(asarray(img, dtype='uint8'))
#            img = colorspace(img)
#            img = cvCreateImageFromNumpyArray(img)
#            print fromarray(img)
#            if nchannels < 3:
#                img = my_pil_to_ipl(fromarray(img), nchannels)
#                img = colorspace(img)
#            else:
#                img = pil_to_ipl(fromarray(img))
#            mat = cvCreateMatNDFromNumpyArray(img)
#            img = cvGetImage(mat)
#            pass
#            FromNumpyArray(img)
#        if swap_rb:
#            cvConvertImage(img, img, CV_CVTIMG_SWAP_RB)
#        print img
#        if swap_rb:
#            cv_swap_rb(img)
#        print img.reshape(960, 960)

        img = self.new_frame(img, swap_rb)
        self.source_frame = img
#        self.current_frame = img.clone()
#        self.frames = [img.clone()]
#        self.frames = [img]

#        self.frames = [clone(img)]

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
#            f = swapRB(f)
#            f = clone(self.source_frame)
#            cv.convertImage(f, f, CV_CVTIMG_SWAP_RB)

        a = f.as_numpy_array()
        if cropbounds:
            a = a[
                cropbounds[0]:cropbounds[1],
                cropbounds[2]:cropbounds[3]
                ]

        return flipud(a)  # [lx / 4:-lx / 4, ly / 4:-ly / 4]

    def get_frame(self, **kw):
#        try:
#            del self._frame
#        except AttributeError:
#            pass

        frame = self._get_frame(**kw)
        frame = self.modify_frame(frame, **kw)
        return frame

    def get_image(self, **kw):
        frame = self.get_frame(**kw)
        return frame.to_pil_image()


    def get_bitmap(self, **kw):  # flip = False, swap_rb = False, mirror = True):
        '''

        '''
#        kw = dict()
#        if swap_rb:
#            kw['flag'] = CV_CVTIMG_SWAP_RB
#        print kw
        frame = self.get_frame(**kw)
        try:
            return frame.to_wx_bitmap()
        except AttributeError:
            pass
#             import wx
#             if frame is not None:
# #                self._frame = frame
#                 return wx.BitmapFromBuffer(frame.width,
#                                        frame.height,
#                                        frame.data_as_string()
#                                         )

    def modify_frame(self, frame, vflip=None, hflip=None , gray=False, swap_rb=None,
                  clone=False, croprect=None, size=None):
#        print size
#        size = (100, 100)
        if frame is not None:
            def _get_param(param, p):
                if param is None:
                    return getattr(self, p)
                else:
#                    setattr(self, p, param)
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

#    @memoized
#    def render_images(self, pychron):
    def render(self):
        return self.frames[0]
#        w = sum([s.size()[0] for s in pychron])
#        h = sum([s.size()[1] for s in pychron])
#        print w,h, pychron[0].size()
        w = self.width
        h = self.height - 15
#        display =
        try:
#            return resize(self.frames[0], w, h, dst=new_dst(w, h, 3))
            return resize(self.frames[0], w, h, dst=(w, h, 3))
        except IndexError:
            pass
#        return display

#        try:
#            s1 = pychron[0].ndarray
#            s2 = pychron[1].ndarray
#        except IndexError:
#            resize(pychron[0], w, h, dst=display)
#            return display
#        except (TypeError, AttributeError):
#            return
#
#        try:
#            s1 = pychron[0].ndarray
#            s2 = pychron[1].ndarray
#
#            npad = 2
#            pad = asMat(zeros((s1.shape[0], npad, s1.shape[2]), 'uint8'))
#            add_scalar(pad, (255, 0, 255))
#
#            s1 = hstack((pad.ndarray, s1))
#            s1 = hstack((s1, pad.ndarray))
#            s1 = hstack((s1, s2))
#            da = hstack((s1, pad.ndarray))
#
#            vpad = asMat(zeros((npad, da.shape[1], da.shape[2]), 'uint8'))
#            add_scalar(vpad, (0, 255, 255))
#            da = vstack((vpad.ndarray, da))
#            da = vstack((da, vpad.ndarray))
#
#            i1 = PILImage.fromarray(da)
#            composite = frompil(i1)
#
#            resize(composite, w, h, dst=display)
#        except TypeError:
#            pass


    def save(self, path, src=None,
#             width=640, height=480
             ):
        if src is None:
            src = self.render()
#            pychron = self.render_images(self.frames)
#        display =

#        cvConvertImage(pychron, pychron, CV_CVTIMG_SWAP_RB)
#        pychron = swapRB(pychron)
#        save_image(resize(pychron, width, height, dst=new_dst(width, height, 3)), path)
#        save_image(resize(pychron, width, height,
#                          dst=(width, height, 3)
#                          ), path)
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


if __name__ == '__main__':
    pass
#======== EOF ================================
