# ===============================================================================
# Copyright 2014 Jake Ross
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


# ============= enthought library imports =======================
from PySide import QtCore, QtGui
from traits.api import Bool, Int, Color, Dict

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.text_editor import SimpleEditor


class _KeywordEditor(SimpleEditor):
    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self.control = QtGui.QTextEdit(self.str_value)
        # self.control = QtGui.TextEdit(self.str_value)
        # self.control= QtGui.QLineEdit(self.str_value)
        QtCore.QObject.connect(self.control,
                               QtCore.SIGNAL('editingFinished()'), self.update_object)

        QtCore.QObject.connect(self.control,
                               QtCore.SIGNAL('cursorPositionChanged()'), self.update_cursor_position)
        self.set_tooltip()

        ctrl = self.control
        ctrl.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Fixed)
        ctrl.setFixedHeight(20)
        if not self.factory.editable:
            ctrl.setReadOnly(True)

        if self.factory.bgcolor:
            p = ctrl.palette()

            p.setColor(QtGui.QPalette.Base, self.factory.bgcolor)
            ctrl.setPalette(p)

        if self.factory.fontsize:
            f = ctrl.font()
            f.setPointSize(self.factory.fontsize)
            ctrl.setFont(f)

    #---------------------------------------------------------------------------
    #  Handles the user changing the contents of the edit control:
    #---------------------------------------------------------------------------

    # def update_object(self):
    #     """ Handles the user changing the contents of the edit control.
    #     """
    #     self.value = unicode(self.control.toPlainText())
    #     # try:
    #     #     pass
    #     # except TraitError, excp:
    #     #     pass
    #
    # def update_editor(self):
    #     self.update_object()

    def update_cursor_position(self):
        user_object = self.context_object
        print user_object


class KeywordEditor(BasicEditorFactory):
    klass = _KeywordEditor
    editable = Bool(True)
    bgcolor = Color
    fontsize = Int
    mapping = Dict
    evaluate = None

# ============= EOF =============================================

# ============= EOF =============================================

