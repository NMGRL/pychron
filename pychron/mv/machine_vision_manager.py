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
from traits.etsconfig.etsconfig import ETSConfig

from pychron.envisage.view_util import open_view

ETSConfig.toolkit = 'qt4'


# ============= enthought library imports =======================
from traits.api import Instance, Float, Any

# ============= standard library imports ========================
from threading import Timer
from numpy import asarray
# ============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.image.video import Video
# from pychron.image.image import StandAloneImage
from pychron.image.cv_wrapper import get_size, crop, grayspace
from pychron.image.standalone_image import StandAloneImage
# from pychron.image.cvwrapper import get_size, crop, grayspace

from pychron.mv.co2_locator import CO2Locator


class MachineVisionManager(Manager):
    video = Instance(Video)
    #     target_image = Instance(StandAloneImage)
    pxpermm = Float(23)
    laser_manager = Any

    def new_co2_locator(self):
        c = CO2Locator(pxpermm=self.pxpermm)
        return c

    def new_image_frame(self):
        if self.video:
            src = self.video.get_frame()
            return src

            # ===============================================================================
            # image manipulation
            # ===============================================================================

    def _crop_image(self, src, cw, ch):
        CX, CY = 0, 0
        cw_px = int(cw * self.pxpermm)
        ch_px = int(ch * self.pxpermm)
        w, h = get_size(src)

        x = int((w - cw_px) / 2 + CX)
        y = int((h - ch_px) / 2 + CY)

        #        print w / self.pxpermm, cw_px / self.pxpermm
        #        ra = 1
        #        print self.pxpermm * ra
        #        print w / float(cw)
        #        self.cpxpermm = w / float(cw) / 2.
        #        print h / float(ch), w / float(cw)
        #        print self.pxpermm * float(w) / cw_px
        #        self.cpxpermm = self.pxpermm * w / cw
        #        print self.cpxpermm, w / cw
        #        print w, cw_px
        #        print cw, w / (cw * self.pxpermm)
        #        self.croppixels = (cw_px, ch_px)
        #        self.croprect = (x, y, cw_px, ch_px)
        #        cw_px = ch_px = 107

        r = 4 - cw_px % 4
        cw_px = ch_px = cw_px + r

        return asarray(crop(src, x, y, cw_px, ch_px))

    def _gray_image(self, src):
        return grayspace(src)

    def view_image(self, im, auto_close=True):
        # use a manager to open so will auto close on quit
        open_view(im)
        if auto_close:
            minutes = 2
            t = Timer(60 * minutes, im.close_ui)
            t.start()

    def new_image(self, frame=None, title='AutoCenter',
                  view_id='target'):

        im = StandAloneImage(title=title,
                             id='pychron.machine_vision.{}'.format(view_id))

        if frame is not None:
            im.load(frame, swap_rb=True)

        return im

# ============= EOF =============================================
