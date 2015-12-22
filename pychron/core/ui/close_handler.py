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
from pyface.qt import QtCore
from traits.api import Bool
from traitsui.api import Handler


# ============= standard library imports ========================
# ============= local library imports  ==========================
class CloseHandler(Handler):
    WINDOW_CNT = 0
    always_on_top = Bool(False)

    def closed(self, info, is_ok):
        # global WINDOW_CNT
        CloseHandler.WINDOW_CNT -= 1
        CloseHandler.WINDOW_CNT = max(0, CloseHandler.WINDOW_CNT)

    def init(self, info):
        # global WINDOW_CNT
        CloseHandler.WINDOW_CNT += 1
        # print WINDOW_CNT
        if self.always_on_top:
            info.ui.control.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

# ============= EOF =============================================
