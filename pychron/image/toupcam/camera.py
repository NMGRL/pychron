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

# ============= enthought library imports =======================
from traits.api import provides
# ============= standard library imports ========================
import ctypes
from numpy import zeros, uint8, uint32
# ============= local library imports  ==========================
from pychron.image.cv_wrapper import save_image
from pychron.image.i_camera import ICamera

lib = ctypes.cdll.LoadLibrary('libtoupcam.dylib')

TOUPCAM_EVENT_EXPOSURE = 1  # exposure time changed
TOUPCAM_EVENT_TEMPTINT = 2  # white balance changed
TOUPCAM_EVENT_CHROME = 3  # reversed, do not use it
TOUPCAM_EVENT_IMAGE = 4  # live image arrived, use Toupcam_PullImage to get this image
TOUPCAM_EVENT_STILLIMAGE = 5  # snap (still) frame arrived, use Toupcam_PullStillImage to get this frame
TOUPCAM_EVENT_ERROR = 80  # something error happens
TOUPCAM_EVENT_DISCONNECTED = 81  # camera disconnected


class HToupCam(ctypes.Structure):
    _fields_ = [('unused', ctypes.c_int)]


def success(r):
    """
        return true if r==0
    :param r:
    :return:
    """
    return r == 0


@provides(ICamera)
class ToupCamCamera(object):
    _data = None
    _frame_fn = None

    def __init__(self, resolution=2, bits=32):
        self.resolution = resolution
        self.cam = self.get_camera()
        self.bits = bits

    # icamera interface
    def save(self, p):
        save_image(self._data, p)

    def get_image_data(self, *args, **kw):
        return self._data

    def close(self):
        if self.cam:
            lib.Toupcam_Close(self.cam)

    def open(self):
        self.set_esize(self.resolution)
        w, h = self.get_size()

        dtype = uint8
        if self.bits == 32:
            dtype = uint32

        self._data = zeros((h.value, w.value, 3), dtype=dtype)

        def get_frame(nEvent, ctx):

            if nEvent == TOUPCAM_EVENT_IMAGE:
                w, h = ctypes.c_uint(), ctypes.c_uint()
                lib.Toupcam_PullImage(self.cam, ctypes.c_void_p(self._data.ctypes.data), bits,
                                      ctypes.byref(w),
                                      ctypes.byref(h))

        CB = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_void_p)

        self._frame_fn = CB(get_frame)

        result = lib.Toupcam_StartPullModeWithCallback(self.cam, self._frame_fn)
        return success(result)

    # ToupCam interface
    def get_camera(self, cid=None):
        func = lib.Toupcam_Open
        func.restype = ctypes.POINTER(HToupCam)
        cam = func(cid)
        return cam

    def get_serial(self):
        sn = ctypes.create_string_buffer(32)
        result = lib.Toupcam_get_SerialNumber(self.cam, sn)
        if success(result):
            sn = sn.value
            return sn

    def get_firmware_version(self):
        fw = ctypes.create_string_buffer(16)
        result = lib.Toupcam_get_FwVersion(self.cam, fw)
        if success(result):
            return fw.value

    def get_hardware_version(self):
        hw = ctypes.create_string_buffer(16)
        result = lib.Toupcam_get_HwVersion(self.cam, hw)
        if success(result):
            return hw.value

    def get_size(self):
        w, h = ctypes.c_long(), ctypes.c_long()

        result = lib.Toupcam_get_Size(self.cam, ctypes.byref(w), ctypes.byref(h))
        if success(result):
            return w, h

    def get_esize(self):
        res = ctypes.c_long()
        result = lib.Toupcam_get_eSize(self.cam, ctypes.byref(res))
        if success(result):
            return res

    def set_esize(self, nres):
        lib.Toupcam_put_eSize(self.cam, ctypes.c_ulong(nres))


# ============= EOF =============================================



