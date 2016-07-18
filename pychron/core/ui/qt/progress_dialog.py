# ===============================================================================
# Copyright 2012 Jake Ross
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
# from pyface.api import ProgressDialog

import sys
import time

from PySide import QtGui
from PySide.QtCore import Qt
from PySide.QtGui import QLabel, QDialogButtonBox
from pyface.ui.qt4.progress_dialog import ProgressDialog
from traits.api import Property, Bool, Int


# ============= local library imports  ==========================


class Stream(object):
    parent = None

    def __init__(self, parent, message_length=50):
        self.message_length = message_length
        self.parent = parent

    def write(self, msg):
        n = self.message_length
        if len(msg) > n:
            msg = '...{}'.format(msg[-n:])
        self.parent.change_message(msg)

    def flush(self):
        pass


class StdoutCTX(object):
    model = None

    def __init__(self, model):
        self.model = model

    def __enter__(self):
        m = Stream(self.model, message_length=60)
        sys.stdout = m
        sys.stderr = m

    def __exit__(self, _type, value, _traceback):
        if self.model:
            self.model.close()
            sys.stdout = sys.__stdout__


class myProgressDialog(ProgressDialog):
    show_percent = True
    show_time = True

    canceled = Property
    accepted = Property
    width = Int(400)
    height = Int(10)
    _user_accepted = Bool(False)
    close_at_end = Bool(True)

    # stream = Instance(Stream)

    def stdout(self):
        return StdoutCTX(self)

    def soft_close(self):
        if self.close_at_end:
            self.close()

    def close(self):
        if self.progress_bar:
            super(myProgressDialog, self).close()

    def cancel(self):
        self._user_cancelled = True
        self.close()

    def accept(self):
        self._user_accepted = True
        self.close()

    def _create_control(self, parent):
        control = super(myProgressDialog, self)._create_control(parent)
        control.resize(self.width, self.height)
        if self.position:
            control.move(*self.position)
        control.setWindowFlags(Qt.WindowStaysOnTopHint)
        return control

    def _create_buttons(self, dialog, layout):
        """ Creates the buttons. """

        if not (self.can_cancel or self.can_ok):
            return

        # Create the button.
        buttons = QDialogButtonBox()

        if self.can_cancel:
            cancel_button = buttons.addButton(self.cancel_button_label, QDialogButtonBox.RejectRole)
            cancel_button.clicked.connect(self.cancel)
        if self.can_ok:
            ok_button = buttons.addButton(QDialogButtonBox.Ok)
            ok_button.clicked.connect(self.accept)

        layout.addWidget(buttons)

    def _get_canceled(self):
        return self._user_cancelled

    def _get_accepted(self):
        return self._user_accepted

    def change_message(self, message, auto_increment=True):
        try:
            self.message_control.setText(message)
            if auto_increment:
                self.increment()
        except RuntimeError, e:
            print 'exception', e

    def _create_message(self, dialog, layout):
        label = QLabel(self.message, dialog)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(label)
        self.message_control = label

    def get_value(self):
        if self.progress_bar:
            return self.progress_bar.value()
        else:
            return 0

    def increment(self, step=1):
        v = self.get_value()
        self.update(v + step)

    def increase_max(self, step=1):
        self.max += step

    def update(self, value):
        """
        updates the progress bar to the desired value. If the value is >=
        the maximum and the progress bar is not contained in another panel
        the parent window will be closed

        """
        if self.progress_bar is None:
            return None, None

        percent = 1.0
        if self.max > 0:
            self.progress_bar.setValue(value)

            if (self.max != self.min):
                percent = (float(value) - self.min) / (self.max - self.min)
            else:
                percent = 1.0

            if value >= self.max or self._user_cancelled:
                self.close()
        else:
            self.progress_bar.setValue(self.progress_bar.value() + value)

            if self._user_cancelled:
                self.close()

        if self.show_time and (percent != 0):
            current_time = time.time()
            elapsed = current_time - self._start_time
            estimated = elapsed / percent
            remaining = estimated - elapsed
            self._set_time_label(elapsed,
                                 self._elapsed_control)
            self._set_time_label(estimated,
                                 self._estimated_control)
            self._set_time_label(remaining,
                                 self._remaining_control)

        if self.show_percent:
            self._percent_control = "%3f" % ((percent * 100) % 1)

        QtGui.QApplication.processEvents()

        return (not self._user_cancelled, False)

# def set_size(self, w, h):
# #        self.dialog_size = QRect(QPoint(0, 0), QSize(w, h))
#         self.size = (w, h)
#         print self.size
# ============= EOF =============================================
