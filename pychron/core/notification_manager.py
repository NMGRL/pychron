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
# ============= standard library imports ========================
import weakref
# ============= local library imports  ==========================
from pychron.core.ui.notification_widget import NotificationWidget


class NotificationManager(object):
    _rect_tuple = None
    parent = None
    def __init__(self, *args, **kw):
        self.messages = []

    def add_notification(self, message, color='orange', fontsize=18):
        parent = self.parent
        if parent:
            parent.moveEvent = self._move
            parent.resizeEvent = self._resize

            prect = parent.geometry()

            dw = NotificationWidget(message,
                                    fontsize=fontsize,
                                    color=color)

            dw.on_close = self._update_positions
            x, y, w, h = prect.x(), prect.y(), prect.width(), prect.height()
            self._rect_tuple = x, y, w, h
            dw.set_position(x, y, w, h)

            # bump messages down
            self._set_positons(x, y, w, h, offset=1)
            self.messages.append(weakref.ref(dw)())

    def _update_positions(self, widget):
        self.messages.remove(widget)
        x, y, w, h = self._rect_tuple
        self._set_positons(x, y, w, h)

    def _move(self, event):
        p = event.pos()
        x, y, w, h = (p.x(), p.y() + 22, self._rect_tuple[2], self._rect_tuple[3])
        self._set_positons(x, y, w, h)

    def _resize(self, event):
        size = event.size()
        x, y, w, h = (self._rect_tuple[0], self._rect_tuple[1], size.width(), size.height())
        self._set_positons(x, y, w, h)

    def _set_positons(self, x, y, w, h, offset=0):
        self._rect_tuple = x, y, w, h
        for i, mi in enumerate(reversed(self.messages)):
            mi.set_position(x, y + mi.height() * (i + offset), w, h)

# ============= EOF =============================================



