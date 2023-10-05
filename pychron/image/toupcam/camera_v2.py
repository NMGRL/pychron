# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= standard library imports ========================
from __future__ import absolute_import
import ctypes
import os
from copy import copy
from io import StringIO
from PIL import Image
from PyQt5.QtGui import QImage
from numpy import zeros, uint8, uint32

# ============= enthought library imports =======================
from qimage2ndarray import recarray_view
from traits.api import provides
from numpy import asarray, array, load, frombuffer
# ============= local library imports  ==========================
from pychron.image.i_camera import ICamera
from pychron.image.toupcam import (
    lib,
    success,
    HToupCam,
    TOUPCAM_EVENT_STILLIMAGE,
    TOUPCAM_EVENT_IMAGE,
)
from pychron.image.toupcam.toupcam import Toupcam


@provides(ICamera)
class ToupCamCamera(object):
    pixel_depth = 3
    hooks = None
    def __init__(self):
        a = Toupcam.EnumV2()
        self.hcam = Toupcam.Open(a[0].id)

    def load_configuration(self, cfg):

        cfg = cfg.get('Device')
        if cfg:
            exp = cfg.get('exposure')
            if exp:
                self._set_auto_exposure(False)
                self._set_exposure(exp)

            hflip = cfg.get('hflip', False)
            self._set_hflip(hflip)

            self._set_esize(cfg.get('size', 0))

        self.w, self.h = self.hcam.get_Size()
        # bufsize = ((self.w * 24 + 31) // 32 * 4) * self.h
        bufsize = self.w*self.h*self.pixel_depth
        self.buf = bytes(bufsize)

        self.hcam.StartPullModeWithCallback(self.cameraCallback, self)

    def cameraCallback(self, nEvent, ctx):
        if nEvent == TOUPCAM_EVENT_IMAGE:
            self.hcam.PullImageV2(self.buf, 24, None)
            if self.hooks:
                # arr = frombuffer(self.buf, dtype=uint8).reshape(self.h, self.w, self.pixel_depth)

                img = QImage(copy(self.buf), self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
                for h in self.hooks:
                    try:
                        h(img)
                    except RuntimeError as e:
                        print(e)
                        # self.hooks = None
                        break

    def read(self):
        arr = frombuffer(self.buf, dtype=uint8).reshape(self.h, self.w, self.pixel_depth)
        self._arr = arr

        return True, self._arr.copy()
    def _set_esize(self, e):
        self.hcam.put_eSize(e)

    def _set_hflip(self, s):
        self.hcam.put_HFlip(s)

    def _set_auto_exposure(self, s):
        self.hcam.put_AutoExpoEnable(s)

    def _set_exposure(self, e):
        self.hcam.put_ExpoTime(int(e*1000))

