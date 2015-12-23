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
from traits.api import Instance, Float, List
# ============= standard library imports ========================
from threading import Timer
# ============= local library imports  ==========================
from pychron.core.ui.close_handler import CloseHandler
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.view_util import open_view
from pychron.loggable import Loggable
from pychron.image.video import Video
from pychron.image.standalone_image import StandAloneImage


def view_image(im, auto_close=True):
    def _func():
        open_view(im)
        if auto_close:
            minutes = 2
            t = Timer(60 * minutes, im.close_ui)
            t.start()

    invoke_in_main_thread(_func)


OX = 50
OY = 50
XOFFSET = 25
YOFFSET = 25


class MachineVisionManager(Loggable):
    video = Instance(Video)
    pxpermm = Float(23)
    open_images = List

    def new_image_frame(self):
        if self.video:
            src = self.video.get_frame()
            return src

    def new_image(self, frame=None, title='AutoCenter',
                  view_id='target'):
        im = StandAloneImage(title=title,
                             handler=CloseHandler(always_on_top=False))
        im.window_x = OX + XOFFSET * CloseHandler.WINDOW_CNT
        im.window_y = OY + YOFFSET * CloseHandler.WINDOW_CNT
        # im.window_height = 200
        # im.window_width = 200
        # im.resizable = True
        if frame is not None:
            im.load(frame, swap_rb=True)
        self.open_images.append(im)
        im.on_trait_change(self._remove_image, 'close_event')
        return im

    def close_open_images(self):
        import time
        for i in self.open_images:
            i.close_ui()
            time.sleep(0.05)

    def _remove_image(self, obj, name, old, new):
        self.open_images.remove(obj)
        obj.on_trait_change(self._remove_image, 'close_event', remove=True)


# ============= EOF =============================================
