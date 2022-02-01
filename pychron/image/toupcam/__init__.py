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
from __future__ import absolute_import
import ctypes
import os
import sys

# ============= local library imports  ==========================

TOUPCAM_EVENT_EXPOSURE = 1  # exposure time changed
TOUPCAM_EVENT_TEMPTINT = 2  # white balance changed
TOUPCAM_EVENT_CHROME = 3  # reversed, do not use it
TOUPCAM_EVENT_IMAGE = 4  # live image arrived, use Toupcam_PullImage to get this image
TOUPCAM_EVENT_STILLIMAGE = (
    5  # snap (still) frame arrived, use Toupcam_PullStillImage to get this frame
)
TOUPCAM_EVENT_ERROR = 80  # something error happens
TOUPCAM_EVENT_DISCONNECTED = 81  # camera disconnected

root = os.path.dirname(__file__)
if sys.platform == "darwin":
    lib = ctypes.cdll.LoadLibrary(os.path.join(root, "osx", "libtoupcam.dylib"))
else:
    directory = "x64" if sys.maxsize > 2**32 else "x84"
    ext = "lib" if sys.platform.startswith("linux") else "dll"
    lib = ctypes.windll.LoadLibrary(
        os.path.join(root, directory, "toupcam.{}".format(ext))
    )


class HToupCam(ctypes.Structure):
    _fields_ = [("unused", ctypes.c_int)]


def success(r):
    """
        return true if r==0
    :param r:
    :return:
    """
    return r == 0


# ============= EOF =============================================
