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
import time

from traits.api import Button, Instance
from traitsui.api import View, Item

from pychron.mv.machine_vision_manager import MachineVisionManager
from pychron.mv.test_image import TestImage


# ============= standard library imports ========================
# ============= local library imports  ==========================

class TestMVManager(MachineVisionManager):
    step = Button
    test_image = Instance(TestImage, ())

    def _step_fired(self):
        self.step_signal.set()

    def traits_view(self):
        return View(Item('test'),
                    Item('step'),
                    Item('test_image', show_label=False,
                         style='custom'),
                    resizable=True
                    )

    def _test_fired(self):
        from pychron.globals import globalv

        p = '/Users/ross/Sandbox/test_target.jpg'
#         p = '/Users/ross/Sandbox/pos_err/pos_err_200_0-002.jpg'
        p = '/Users/ross/Sandbox/poserror/pos_err_221_0-007.jpg'
#         p = '/Users/ross/Sandbox/poserror/snapshot009.jpg'
        # force video to reload test image
        self.video.source_frame = None
        globalv.video_test_path = p

        im = self.setup_image()

#         self._test2(im)
        from pychron.core.ui.thread import Thread
        t = Thread(target=self._test2, args=(im,))
        t.start()
        self._t = t

# ===============================================================================
# tests
# ===============================================================================
    def _test(self, im):

        paths = (
#                 ('/Users/ross/Sandbox/pos_err/snapshot007.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_221_0-005.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_207_0-002.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_209_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_210_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_220_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_221_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_221_0-002.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_221_0-003.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_221_0-004.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_200_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_200_0-002.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_201_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_202_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_203_0-001.jpg', 1.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_204_0-001.jpg', 1.25),
                 ('/Users/ross/Sandbox/pos_err/pos_err_206_0-001.jpg', 1.25),
#                  ('/Users/ross/Sandbox/pos_err/pos_err_206_1-001.jpg', 1.25),
#                  ('/Users/ross/Sandbox/pos_err/pos_err_207_0-001.jpg', 1.25),
#                  ('/Users/ross/Sandbox/pos_err/pos_err_52001.jpg', 2.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_52001.tiff', 2.25),
#                  ('/Users/ross/Sandbox/pos_err/pos_err_52002.jpg', 2.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_53001.jpg', 2.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_53002.jpg', 2.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_53003.jpg', 2.25),
#                 ('/Users/ross/Sandbox/pos_err/pos_err_54001.jpg', 2.25),
                )
        fails = 0
        times = []

#         im = self.target_image
        for p, dim in paths[:]:
            from pychron.globals import globalv
            # force video to reload test image
            self.video.source_frame = None
            globalv.video_test_path = p
#             return
#             im.source_frame = self.new_image_frame()
            frm = self.new_image_frame()
#             self.target_image.load()

            cw = ch = dim * 3.2
#            cw = ch = dim
            frame = self._crop_image(frm, cw, ch)
            im.source_frame = frame
#            time.sleep(1)
#            continue
#            self.target_image.set_frame(0, frame)

#            loc.pxpermm = self.cpxpermm

#            loc.croppixels = (cw * self.pxpermm, ch * self.pxpermm)

            loc = self.new_co2_locator()

            st = time.time()
            dx, dy = loc.find(im, frame, dim * self.pxpermm)

            times.append(time.time() - st)
            if dx and dy:
                self.info('SUCCESS path={}'.format(p))
                self.info('calculated deviation {:0.3f},{:0.3f}'.format(dx, dy))
            else:
                fails += 1
                self.info('FAIL    path={}'.format(p))
            time.sleep(1)

        if times:
            n = len(paths)
            self.info('failed to find center {}/{} times'.format(fails, n))
            self.info('execution times: min={} max={} avg={}'.format(min(times), max(times), sum(times) / n))

#        def foo():
#            from pylab import show, plot
#            plot(times)
#            show()
#        do_later(foo)

    def _test2(self, im):

        dim = 1.0

        frame = self.new_image_frame()

        cw = ch = dim * 3.2

        frame = self._crop_image(frame, cw, ch)
#         print frame
#         im.source_frame = frame
        loc = self.new_co2_locator()
        from threading import Event
        evt = Event()
        self.step_signal = evt
        loc.step_signal = evt
        loc.test_image = self.test_image

        dx, dy = loc.find(im, frame, dim * self.pxpermm)
#         print dx, dy
    def setup_image(self):
        frame = self.new_image_frame()
        im = self.new_image(frame)
        self.view_image(im)
        return im

def test1():
    from pychron.image.video import Video
    from pychron.globals import globalv
    globalv.video_test = True
    globalv.video_test_path = '/Users/ross/Sandbox/pos_err/snapshot007.jpg'
#    globalv.video_test_path = '/Users/ross/Sandbox/pos_err/pos_err_53002.jpg'
    globalv.video_test_path = '/Users/ross/Sandbox/pos_err/pos_err_221_0-005.jpg'

#    globalv.video_test_path = '/Users/ross/Sandbox/pos_err/diodefailsnapshot.jpg'
    video = Video()
    video.open()
    mv = MachineVisionManager(video=video)
    mv.configure_traits()


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('mv')
    test()
# ============= EOF =============================================
