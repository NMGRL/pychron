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
# ============= enthought library imports =======================
# ============= standard library imports ========================
import time
from threading import Event, currentThread, Thread

from pyface.api import OK, YES
from pyface.i_dialog import MDialog
from pyface.message_dialog import MessageDialog
from pyface.qt import QtGui
from pyface.qt.QtCore import Qt
from pyface.qt.QtGui import QMessageBox, QPrintDialog, QPrinter
from pyface.qt.QtGui import QSizePolicy, QCheckBox
from pyface.ui.qt.confirmation_dialog import ConfirmationDialog
from pyface.ui.qt.dialog import Dialog
from pyface.ui.qt.window import Window

# ============= local library imports  ==========================
from traits.api import Str

from pychron.core.ui.gui import invoke_in_main_thread


class PrinterDialog(Dialog):
    printer = None

    def is_landscape(self):
        layout = self.printer.pageLayout()
        return bool(layout.orientation())

    def pagesize(self):
        r = self.printer.pageRect()
        return r.width(), r.height()

    def print_enabled(self):
        return self.return_code == 10

    def open(self):
        super(PrinterDialog, self).open()
        return self.print_enabled()

    def _create_control(self, parent):
        dlg = QPrintDialog(parent=parent)
        self.control = dlg
        return dlg

    def _create_contents(self, control):
        pass

    def close(self, force=False):
        self.printer = self.control.printer()
        super(PrinterDialog, self).close(force=force)


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
        from threading import _MainThread

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
                    t = "{}\n\nTimeout in {:n}s".format(self.message, int(timeout - et))
                    invoke_in_main_thread(self.control.setText, t)

    def _open(self, evt):
        if self.control is None:
            self._create()

        if self.style == "modal":
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


class myConfirmationDialog(myMessageMixin, ConfirmationDialog):
    default_button = "yes"

    def _create_control(self, parent):
        dlg = super(myConfirmationDialog, self)._create_control(parent)

        if self.size != (-1, -1):
            dlg.resize(*self.size)

        dlg.buttonClicked.connect(self._handle_button)
        if self.default_button == "yes":
            dlg.setDefaultButton(QMessageBox.Yes)
        else:
            dlg.setDefaultButton(QMessageBox.No)

        return dlg

    def _handle_button(self, evt):
        if self._closed_evt:
            self._closed_evt.set()


class RememberConfirmationDialog(myConfirmationDialog):
    def _create_control(self, parent):
        dlg = super(RememberConfirmationDialog, self)._create_control(parent)

        dlg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.size != (-1, -1):
            dlg.resize(*self.size)
            dlg.event = self._handle_evt

        # dlg.buttonClicked.connect(self._handle_button)

        cb = QCheckBox("Remember this choice")
        lay = dlg.layout()
        lay.addWidget(cb)
        self.cb = cb
        return dlg

    @property
    def remember(self):
        return self.cb.checkState() == Qt.Checked


class CustomizableDialog(Dialog):
    message = Str

    def _create_buttons(self, parent):
        buttons = QtGui.QDialogButtonBox()

        # 'OK' button.
        if self.ok_label:
            btn = buttons.addButton(self.ok_label, QtGui.QDialogButtonBox.AcceptRole)
        else:
            btn = buttons.addButton(QtGui.QDialogButtonBox.Ok)

        btn.setDefault(True)
        btn.clicked.connect(self.control.accept)

        return buttons

    def _create_dialog_area(self, parent):
        label = QtGui.QLabel()

        label.setTextFormat(Qt.RichText)
        label.setText(self.message)
        return label


# ============= EOF =============================================
