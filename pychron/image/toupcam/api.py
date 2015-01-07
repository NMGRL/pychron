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
# ============= standard library imports ========================
from ctypes import cdll, byref
from numpy import zeros
# ============= local library imports  ==========================


lib = cdll.LoadLibrary('libtoupcam.dylib')


def enumerate_cameras():
    for i in range(lib.Toupcam_Enum()):
        print i


def get_camera(cid=None):
    return lib.Toupcam_Open(cid)


def get_frame(cobj):
    frame = zeros((480, 640, 3), dtype=int)
    lib.Toupcam_PullImage(cobj, byref(frame))
    return frame


# ============= EOF =============================================



