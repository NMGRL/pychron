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

import warnings
warnings.warn("deprecated. Use ToupCamCamera instead", DeprecationWarning)


# ============= enthought library imports =======================
# ============= standard library imports ========================
import ctypes
from numpy import zeros, uint8, uint32
# ============= local library imports  ==========================




lib = ctypes.cdll.LoadLibrary('libtoupcam.dylib')

c_int_p = ctypes.POINTER(ctypes.c_int)


class HToupCam(ctypes.Structure):
    _fields_ = [('unused', ctypes.c_int)]


def success(r):
    """
        return true if r==0
    :param r:
    :return:
    """
    return r == 0


def get_camera(cid=None):
    func = lib.Toupcam_Open
    func.restype = ctypes.POINTER(HToupCam)
    cam = func(cid)
    return cam


def get_serial(cobj):
    sn = ctypes.create_string_buffer(32)
    result = lib.Toupcam_get_SerialNumber(cobj, sn)
    if success(result):
        sn = sn.value
        return sn


def get_firmware_version(cobj):
    fw = ctypes.create_string_buffer(16)
    result = lib.Toupcam_get_FwVersion(cobj, fw)
    if success(result):
        return fw.value


def get_hardware_version(cobj):
    hw = ctypes.create_string_buffer(16)
    result = lib.Toupcam_get_HwVersion(cobj, hw)
    if success(result):
        return hw.value


def get_size(cobj):
    w, h = ctypes.c_long(), ctypes.c_long()

    result = lib.Toupcam_get_Size(cobj, ctypes.byref(w), ctypes.byref(h))
    if success(result):
        return w, h


def get_esize(cobj):
    res = ctypes.c_long()
    result = lib.Toupcam_get_eSize(cobj, ctypes.byref(res))
    if success(result):
        return res


def set_esize(cobj, nres):
    lib.Toupcam_put_eSize(cobj, ctypes.c_ulong(nres))


def start(cobj, draw_cb, resolution=2, bits=32):
    set_esize(cobj, resolution)
    w, h = get_size(cobj)

    dtype = uint8
    if bits == 32:
        dtype = uint32

    data = zeros((h.value, w.value, 3), dtype=dtype)

    def func(cobj, draw_cb):
        def frame_fn(nEvent, ctx):
            if nEvent == 4:
                w, h = ctypes.c_uint(), ctypes.c_uint()
                result = lib.Toupcam_PullImage(cobj, ctypes.c_void_p(data.ctypes.data), bits, ctypes.byref(w),
                                               ctypes.byref(h))
                if success(result):
                    draw_cb(data)

        return frame_fn

    CB = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_void_p)

    # make global to prevent garbage collection
    global _frame_fn
    _frame_fn = CB(func(cobj, draw_cb))

    result = lib.Toupcam_StartPullModeWithCallback(cobj, _frame_fn)
    return success(result)




if __name__ == '__main__':
    cam = get_camera()
    start(cam, lambda x: 1)
    import time

    for i in range(100):
        time.sleep(0.25)
        # print get_serial(cam)
        # print get_size(cam)
        # print get_esize(cam)
        # print get_firmware_version(cam)
        # print get_hardware_version(cam)

        # print get_serial(cam)
        # size = get_frame_size(cam)
        # time.sleep(1)

        # frame = get_frame(cam)
        # print frame.sum()

        # time.sleep(1)
        # frame = get_frame(cam)
        # print frame.sum()
        # print frame
# ============= EOF =============================================



