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
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.notification_widget import NotificationWidget


class NotificationManager(object):
    _rect_tuple = None
    parent = None
    spacing = 5

    def __init__(self, *args, **kw):
        self.messages = []

    def add_notification(self, *args, **kw):
        invoke_in_main_thread(self._add_notification, *args, **kw)

    def _add_notification(self, message, color='orange', fontsize=18):
        parent = self.parent
        if parent:
            parent.resizeEvent = self._resize
            prect = parent.geometry()
            x, y, w, h = prect.x(), prect.y(), prect.width(), prect.height()
            self._rect_tuple = x, y, w, h

            dw = NotificationWidget(message,
                                    parent=parent,
                                    fontsize=fontsize,
                                    color=color)

            dw.on_close = self._update_positions
            self.messages.insert(0, weakref.ref(dw)())

            # bump messages down
            self._message_inserted()

            if len(self.messages) > 5:
                m = self.messages.pop()
                m.destroy()
                m.close()


    def _update_positions(self, widget):
        self.messages.remove(widget)
        if self.messages:
            self._compress_messages()

    def _resize(self, event):
        size = event.size()
        self._rect_tuple = (self._rect_tuple[0], self._rect_tuple[1], size.width(), size.height())
        if self.messages:
            self._reposition()

    def _reposition(self):

        x, y, w, h = self._rect_tuple
        mo = self.messages[0]

        mo.move(w - mo.width(), 0)
        if len(self.messages) > 1:
            for mi in self.messages[1:]:
                mi.move(w - mi.width(), mi.y())

    def _compress_messages(self):
        mo = self.messages[0]
        x, y, w, h = self._rect_tuple
        spacing=self.spacing
        mo.move(w - mo.width(), 0)
        if len(self.messages) > 1:
            hh = 0
            for i, mi in enumerate(self.messages[1:]):
                mo = self.messages[i]

                hh += mo.height() + spacing
                mi.move(w - mi.width(), hh)

    def _message_inserted(self):
        x, y, w, h = self._rect_tuple
        if len(self.messages) > 1:
            mo = self.messages[0]
            spacing = self.spacing
            for i, mi in enumerate(self.messages[1:]):
                y2 = mi.y() + mo.height() + spacing
                mi.move(w-mi.width(), y2)
                # mi.set_position(0, y2, w, h)

# ============= EOF =============================================



