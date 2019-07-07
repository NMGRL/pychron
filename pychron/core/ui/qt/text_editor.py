# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import
from __future__ import print_function

import six
from pyface.qt import QtGui
from traits.api import Bool, Int, Color, Str
from traits.trait_errors import TraitError
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class _TextEditor(Editor):
    fontsize = Int

    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        if self.factory.multiline:
            control = QtGui.QPlainTextEdit(self.str_value)
            if not self.factory.wrap:
                control.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        else:
            control = QtGui.QLineEdit(self.str_value)

        if self.factory.auto_set:
            if isinstance(control, QtGui.QPlainTextEdit):
                control.textChanged.connect(self.update_object)
                # QtCore.QObject.connect(ctrl,
                #                        QtCore.SIGNAL('textChanged()'), self.update_object)
            else:
                # QtCore.QObject.connect(ctrl,
                #                        QtCore.SIGNAL('textEdited(QString)'), self.update_object)
                control.textEdited.connect(self.update_object)
        else:
            # QtCore.QObject.connect(ctrl,
            #                    QtCore.SIGNAL('editingFinished()'), self.update_object)
            control.editingFinished.connect(self.update_object)

        if not self.factory.editable:
            control.setReadOnly(True)

        if self.factory.bgcolor:
            p = control.palette()

            p.setColor(QtGui.QPalette.Base, self.factory.bgcolor)
            control.setPalette(p)

        if self.factory.fontsize:
            f = control.font()
            f.setPointSize(self.factory.fontsize)
            f.setFamily(self.factory.fontname)

            control.setFont(f)

        if self.factory.tab_width:
            f = control.font()
            metrics = QtGui.QFontMetrics(f)
            control.setTabStopWidth(self.factory.tab_width * metrics.width(' '))

        if self.factory.placeholder:
            control.setPlaceholderText(self.factory.placeholder)

        self.sync_value(self.factory.fontsize_name, 'fontsize', mode='from')
        self.set_tooltip()

        self.control = control

    # ---------------------------------------------------------------------------
    #  Handles the user changing the contents of the edit control:
    # ---------------------------------------------------------------------------
    def _fontsize_changed(self):
        ctrl = self.control
        f = ctrl.font()
        f.setPointSize(self.fontsize)
        ctrl.setFont(f)

    def update_object(self):
        """ Handles the user changing the contents of the edit control.
        """
        if isinstance(self.control, QtGui.QLineEdit):
            self.value = six.text_type(self.control.text())
        else:
            try:
                self.value = six.text_type(self.control.document().toPlainText())
            except TraitError as excp:
                print('mytexteditor {}'.format(excp))

    def update_editor(self):
        new_value = self.str_value
        ctrl = self.control
        if isinstance(ctrl, QtGui.QLineEdit):
            self.control.setText(new_value)
        else:
            if self.control.toPlainText() != new_value:
                self.control.setPlainText(new_value)


class myTextEditor(BasicEditorFactory):
    klass = _TextEditor
    wrap = Bool
    tab_width = Int
    editable = Bool(True)
    bgcolor = Color
    fontsize = Int
    fontsize_name = Str
    fontname = 'courier'
    placeholder = Str
    multiline = Bool(True)
    auto_set = Bool(True)


# ============= EOF =============================================
