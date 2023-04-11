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
from io import StringIO
from PIL import Image
from numpy import zeros, uint8, uint32

# ============= enthought library imports =======================
from traits.api import provides

# ============= local library imports  ==========================
from pychron.image.i_camera import ICamera
from pychron.image.toupcam import (
    lib,
    success,
    HToupCam,
    TOUPCAM_EVENT_STILLIMAGE,
    TOUPCAM_EVENT_IMAGE,
)


@provides(ICamera)
class ToupCamCamera(object):
    _data = None
    _frame_fn = None
    _temptint_cb = None
    _save_path = None

    def __init__(self, resolution=2, bits=32):
        if bits not in (32,):
            raise ValueError("Bits needs to by 8 or 32")
        # bits = 8
        self.resolution = resolution
        self.cam = self.get_camera()
        self.bits = bits

    # icamera interface
    def save(self, p, extension="JPEG", *args, **kw):
        # self._save_path = p
        # lib.Toupcam_Snap(self.cam, self.resolution)
        image = self.get_pil_image()

        image.save(p, extension, *args, **kw)

    def _do_save(self, im):
        # raw = im.view(uint8).reshape(im.shape+(-1,))
        # bgr = raw[...,:3]
        # image = pil.fromarray(bgr, 'RGB')
        # b,g,r = image.split()
        # image = pil.merge('RGB', (r,g,b))
        # image = self.get_jpeg_data(im, 10)
        image = self.get_pil_image(im)
        # image.save(self._save_path, 'JPEG', quality=90)
        image.save(self._save_path)
        # view_file(self._save_path)

    def save_jpeg(self, p, quality=100):
        im = self.get_pil_image()
        im.save(p, "JPEG", quality=quality)

    def save_tiff(self, p):
        im = self.get_pil_image()
        im.save(p, "TIFF")

    def get_jpeg_data(self, data=None, quality=75):
        im = self.get_pil_image(data)

        s = StringIO()
        im.save(s, "JPEG", quality=quality)
        s.seek(0, os.SEEK_END)

        return s.getvalue()

    def get_pil_image(self, data=None):
        # im = self._data
        if data is None:
            data = self._data

        raw = data.view(uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        image = Image.fromarray(bgr, "RGB")
        b, g, r = image.split()
        return Image.merge("RGB", (r, g, b))

    def read(self):
        return True, self.get_image_data()

    def get_image_data(self, *args, **kw):
        d = self._data
        return d

    def close(self):
        if self.cam:
            lib.Toupcam_Close(self.cam)

    def open(self):
        self.set_esize(self.resolution)
        args = self.get_size()
        if not args:
            return

        h, w = args[1].value, args[0].value

        shape = (h, w)
        if self.bits == 8:
            dtype = uint8
        else:
            dtype = uint32

        self._data = zeros(shape, dtype=dtype)

        self._cnt = 0

        def get_frame(nEvent, ctx):
            if nEvent == TOUPCAM_EVENT_IMAGE:
                w, h = ctypes.c_uint(), ctypes.c_uint()
                bits = ctypes.c_int(self.bits)

                lib.Toupcam_PullImage(
                    self.cam,
                    ctypes.c_void_p(self._data.ctypes.data),
                    bits,
                    ctypes.byref(w),
                    ctypes.byref(h),
                )

            elif nEvent == TOUPCAM_EVENT_STILLIMAGE:
                w, h = self.get_size()
                h, w = h.value, w.value

                dtype = uint32
                shape = (h, w)

                still = zeros(shape, dtype=dtype)
                bits = ctypes.c_int(self.bits)
                lib.Toupcam_PullStillImage(
                    self.cam, ctypes.c_void_p(still.ctypes.data), bits, None, None
                )
                self._do_save(still)

        CB = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_void_p)

        self._frame_fn = CB(get_frame)

        result = lib.Toupcam_StartPullModeWithCallback(self.cam, self._frame_fn)

        return success(result)

    # ToupCam interface
    def _lib_func(self, func, *args, **kw):
        ff = getattr(lib, "Toupcam_{}".format(func))
        result = ff(self.cam, *args, **kw)
        return success(result)

    def _lib_get_func(self, func):
        v = ctypes.c_int()
        if self._lib_func("get_{}".format(func), ctypes.byref(v)):
            return v.value

    # setters
    def set_gamma(self, v):
        self._lib_func("put_Gamma", ctypes.c_int(v))

    def set_contrast(self, v):
        self._lib_func("put_Contrast", ctypes.c_int(v))

    def set_brightness(self, v):
        self._lib_func("put_Brightness", ctypes.c_int(v))

    def set_saturation(self, v):
        self._lib_func("put_Saturation", ctypes.c_int(v))

    def set_hue(self, v):
        self._lib_func("put_Hue", ctypes.c_int(v))

    def set_exposure_time(self, v):
        self._lib_func("put_ExpoTime", ctypes.c_ulong(v))

    # getters
    def get_gamma(self):
        return self._lib_get_func("Gamma")

    def get_contrast(self):
        return self._lib_get_func("Contrast")

    def get_brightness(self):
        return self._lib_get_func("Brightness")

    def get_saturation(self):
        return self._lib_get_func("Saturation")

    def get_hue(self):
        return self._lib_get_func("Hue")

    def get_exposure_time(self):
        return self._lib_get_func("ExpoTime")

    def do_awb(self, callback=None):
        """
        Toupcam_AwbOnePush(HToupCam h, PITOUPCAM_TEMPTINT_CALLBACK fnTTProc, void* pTTCtx);
        :return:
        """

        def temptint_cb(temp, tint):
            if callback:
                callback((temp, tint))

        CB = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_void_p)
        self._temptint_cb = CB(temptint_cb)

        return self._lib_func("AwbOnePush", self._temptint_cb)

    def set_temperature_tint(self, temp, tint):
        lib.Toupcam_put_TempTint(self.cam, temp, tint)

    def get_temperature_tint(self):
        temp = ctypes.c_int()
        tint = ctypes.c_int()
        if self._lib_func("get_TempTint", ctypes.byref(temp), ctypes.byref(tint)):
            return temp.value, tint.value

    def get_auto_exposure(self):
        expo_enabled = ctypes.c_bool()
        result = lib.Toupcam_get_AutoExpoEnable(self.cam, ctypes.byref(expo_enabled))
        if success(result):
            return expo_enabled.value

    def set_auto_exposure(self, expo_enabled):
        lib.Toupcam_put_AutoExpoEnable(self.cam, expo_enabled)

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


if __name__ == "__main__":
    import time

    cam = ToupCamCamera()
    cam.open()
    time.sleep(1)

    cam.save("foo.jpg")

# ============= EOF =============================================
