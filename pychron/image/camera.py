# ===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from numpy import asarray

from traits.api import HasTraits, provides
# ============= standard library imports ========================
import inspect
# ============= local library imports  ==========================
from pychron.image.cv_wrapper import save_image, get_capture_device, resize, swap_rb
from pychron.image.i_camera import ICamera


@provides(ICamera)
class Camera(HasTraits):
    _device = None
    _owners = None

    def close(self):
        pass

    def open(self, owner=None):
        self._device = get_capture_device()
        self._device.open(0)

        if self._owners is None:
            self._owners = []

        if owner is None:
            stack = inspect.stack()

            # cstack = stack[0]
            rstack = stack[1]

            owner = hash(rstack[3])

        if owner not in self._owners:
            self._owners.append(owner)

    def retrieve_frame(self):
        """
            get a raw frame from the device
        :return:
        """
        if self._device:
            state, img = self._device.read()
            if state:
                return img

    def render_frame(self, src=None, size=None):
        """
            render the raw frame into the final version. i.e flip,rotate, swap channels etc
        :return:
        """
        if src is None:
            src = self.retrieve_frame()

        img = self.post_process(src, size=size)
        return img

    def get_image_data(self, *args, **kw):
        img = self.render_frame(*args, **kw)
        return asarray(img)

    def post_process(self, img, size=None, swap=True):
        if img is not None:
            if size:
                img = resize(img, *size)

            if swap:
                img = swap_rb(img)
        return img

    def save(self, path, src=None):
        if src is None:
            src = self.render_frame()

        save_image(src, path)

# ============= EOF =============================================



