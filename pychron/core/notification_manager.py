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
from traits.api import HasTraits, Button, List
from traitsui.api import View, Item
# ============= standard library imports ========================
import weakref
# ============= local library imports  ==========================
from pychron.core.ui.notification_widget import NotificationWidget


class NotificationManager(object):
    def __init__(self, *args, **kw):
        self.messages = []

    def add_notification(self, parent, message, color='orange', fontsize=18):
        prect = parent.geometry()

        dw = NotificationWidget(message,
                                fontsize=fontsize,
                                color=color)

        x, y, w, h = prect.x(), prect.y(), prect.width(), prect.height()
        dw.set_position(x, y, w, h)

        # bump messages down
        for i, mi in enumerate(reversed(self.messages)):
            mi.set_position(x, y + mi.height() * (i + 1), w, h)

        dw.show()
        self.messages.append(weakref.ref(dw)())

# ============= EOF =============================================



