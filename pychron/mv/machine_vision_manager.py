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
from traits.api import Instance, Float, Any
# ============= standard library imports ========================
from threading import Timer
# ============= local library imports  ==========================
from pychron.envisage.view_util import open_view
from pychron.loggable import Loggable
from pychron.image.video import Video
from pychron.image.standalone_image import StandAloneImage


def view_image(im, auto_close=True):
    open_view(im)
    if auto_close:
        minutes = 2
        t = Timer(60 * minutes, im.close_ui)
        t.start()


class MachineVisionManager(Loggable):
    video = Instance(Video)
    pxpermm = Float(23)

    def new_image_frame(self):
        if self.video:
            src = self.video.get_frame()
            return src

    def new_image(self, frame=None, title='AutoCenter',
                  view_id='target'):
        im = StandAloneImage(title=title,
                             id='pychron.machine_vision.{}'.format(view_id))

        if frame is not None:
            im.load(frame, swap_rb=True)

        return im

# ============= EOF =============================================
# # ===============================================================================
# # image manipulation
# # ===============================================================================
#     def _crop_image(self, src, cw, ch):
#         CX, CY = 0, 0
#         cw_px = int(cw * self.pxpermm)
#         ch_px = int(ch * self.pxpermm)
#         w, h = get_size(src)
#
#         x = int((w - cw_px) / 2 + CX)
#         y = int((h - ch_px) / 2 + CY)
#
# #        print w / self.pxpermm, cw_px / self.pxpermm
# #        ra = 1
# #        print self.pxpermm * ra
# #        print w / float(cw)
# #        self.cpxpermm = w / float(cw) / 2.
# #        print h / float(ch), w / float(cw)
# #        print self.pxpermm * float(w) / cw_px
# #        self.cpxpermm = self.pxpermm * w / cw
# #        print self.cpxpermm, w / cw
# #        print w, cw_px
# #        print cw, w / (cw * self.pxpermm)
# #        self.croppixels = (cw_px, ch_px)
# #        self.croprect = (x, y, cw_px, ch_px)
# #        cw_px = ch_px = 107
#
#         r = 4 - cw_px % 4
#         cw_px = ch_px = cw_px + r
#
#         return asarray(crop(src, x, y, cw_px, ch_px))
#
#     def _gray_image(self, src):
#         return grayspace(src)