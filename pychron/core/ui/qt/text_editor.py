#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from PySide import QtCore, QtGui
from traits.api import Bool, Int, Color, Str
from traits.trait_errors import TraitError

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class _TextEditor(Editor):
    fontsize = Int
    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self.control = QtGui.QPlainTextEdit(self.str_value)
        QtCore.QObject.connect(self.control,
                               QtCore.SIGNAL('editingFinished()'), self.update_object)
        self.set_tooltip()

        ctrl = self.control
        if not self.factory.wrap:
            ctrl.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)

        if self.factory.tab_width:
            ctrl.setTabStopWidth(self.factory.tab_width * 6.0)

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
        self.sync_value(self.factory.fontsize_name, 'fontsize', mode='from')

    #---------------------------------------------------------------------------
    #  Handles the user changing the contents of the edit control:
    #---------------------------------------------------------------------------
    def _fontsize_changed(self):
        ctrl = self.control
        f = ctrl.font()
        f.setPointSize(self.fontsize)
        ctrl.setFont(f)

    def update_object(self):
        """ Handles the user changing the contents of the edit control.
        """
        try:
            self.value = unicode(self.control.text())
        except TraitError, excp:
            pass

    def update_editor(self):
        pass


class myTextEditor(BasicEditorFactory):
    klass = _TextEditor
    wrap = Bool
    tab_width = Int
    editable = Bool
    bgcolor = Color
    fontsize = Int
    fontsize_name = Str

#============= EOF =============================================
