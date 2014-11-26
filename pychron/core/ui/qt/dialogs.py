# ===============================================================================
# Copyright 2012 Jake Ross
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
# ===============================================================================
# from traits.api import HasTraits
import time
from threading import Event, currentThread, _MainThread, Thread

from PySide.QtGui import QSizePolicy
from pyface.api import OK, YES
from pyface.ui.qt4.confirmation_dialog import ConfirmationDialog
from pyface.message_dialog import MessageDialog

from pychron.core.ui.gui import invoke_in_main_thread







#from pyface.confirmation_dialog import ConfirmationDialog

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
class myMessageMixin(object):
    """
        makes  message dialogs thread save.
    """
    timeout_return_code = YES
    _closed_evt = None

    def open(self, timeout=0):
        """
            open the confirmation dialog on the GUI thread but wait for return
        """

        evt = Event()
        ct = currentThread()
        if isinstance(ct, _MainThread):
            if timeout:
                t = Thread(target=self._timeout_loop, args=(timeout, evt))
                t.start()
            self._open(evt)
        else:
            invoke_in_main_thread(self._open, evt)
            self._timeout_loop(timeout, evt)

        return self.return_code

    def _timeout_loop(self, timeout, evt):
        st = time.time()
        while not evt.is_set():
            time.sleep(0.25)
            if timeout:
                et = time.time() - st - 1
                if et > timeout - 1:
                    invoke_in_main_thread(self.destroy)
                    return self.timeout_return_code
                if self.control:
                    t = '{}\n\nTimeout in {:n}s'.format(self.message, int(timeout - et))
                    invoke_in_main_thread(self.control.setText, t)

    def _open(self, evt):
        if self.control is None:
            self._create()

        if self.style == 'modal':
            try:
                self.return_code = self._show_modal()
            except AttributeError:
                pass
            finally:
                self.close()

        else:
            self.show(True)
            self.return_code = OK

        evt.set()
        return self.return_code


class myMessageDialog(myMessageMixin, MessageDialog):
    pass


class _ConfirmationDialog(ConfirmationDialog):
    def _create_control(self, parent):
        dlg = super(_ConfirmationDialog, self)._create_control(parent)
        dlg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.size != (-1, -1):
            dlg.resize(*self.size)
            dlg.event = self._handle_evt

        dlg.buttonClicked.connect(self._handle_button)
        return dlg

    def _handle_button(self, evt):
        if self._closed_evt:
            self._closed_evt.set()

    def _handle_evt(self, evt):
        return True

    def _show_modal(self):
        self.control.setModal(True)
        # self.control.setWindowModality(QtCore.Qt.ApplicationModal)
        retval = self.control.exec_()
        clicked_button = self.control.clickedButton()
        if clicked_button in self._button_result_map:
            retval = self._button_result_map[clicked_button]
            # else:
            #     retva
            # retval = _RESULT_MAP[retval]
        return retval


class myConfirmationDialog(myMessageMixin, _ConfirmationDialog):
    pass


# ============= EOF =============================================
