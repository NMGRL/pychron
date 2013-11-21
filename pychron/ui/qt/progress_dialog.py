#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
# from pyface.api import ProgressDialog

from traits.api import Property, Bool, Int
#============= standard library imports ========================
from PySide.QtCore import Qt
from PySide.QtGui import QLabel, QDialogButtonBox
from pyface.ui.qt4.progress_dialog import ProgressDialog
#============= local library imports  ==========================

class myProgressDialog(ProgressDialog):
    show_percent = True
    show_time = True

    canceled = Property
    accepted = Property
    width = Int(400)
    height = Int(10)
    _user_accepted = Bool(False)

    def close(self):
        try:
            super(myProgressDialog, self).close()
        except AttributeError:
            #window already closed
            pass

    def cancel(self):
        self._user_cancelled = True
        self.close()

    def accept(self):
        self._user_accepted = True
        self.close()

    def _create_control(self, parent):
        control = super(myProgressDialog, self)._create_control(parent)
        control.resize(self.width, self.height)
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
    #         print message
        self.message = message
        try:
            self.message_control.setText(message)
            if auto_increment:
                self.increment()
        except RuntimeError, e:
            print e

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

#     def set_size(self, w, h):
# #        self.dialog_size = QRect(QPoint(0, 0), QSize(w, h))
#         self.size = (w, h)
#         print self.size
#============= EOF =============================================
