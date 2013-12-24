#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
import os
from PySide.QtGui import QSound

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.paths import paths
__SOUNDS__={}


def _get_sound(name):
    so=None
    if name in __SOUNDS__:
        so=__SOUNDS__[name]
    else:
        for r in paths.sound_search_path:
            if os.path.exists(r):
                so = QSound(os.path.join(r, add_extension(name, '.wav')))
                __SOUNDS__[name] = so
                break
    return so


def play_sound(name):
    so=_get_sound(name)
    if so:
        so.play()

#============= EOF =============================================

