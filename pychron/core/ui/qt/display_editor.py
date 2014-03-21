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
from Queue import Empty

from traits.api import Color, Str, Event, Int
from traitsui.qt4.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
from pyface.qt.QtGui import QPlainTextEdit, QTextCursor, QPalette, QColor, QFont


#============= standard library imports ========================
#============= local library imports  ==========================


class _DisplayEditor(Editor):
    clear = Event
    refresh = Event
    control_klass = QPlainTextEdit
    font_size = Int
    bgcolor = Color
    text_width = Int

    def init(self, parent):
        if self.control is None:
            self.control = self.control_klass()
            self.control.setReadOnly(True)

        if self.factory.max_blocks:
            self.control.setMaximumBlockCount(self.factory.max_blocks)

        self.sync_value(self.factory.clear, 'clear', mode='from')
        self.sync_value(self.factory.refresh, 'refresh', mode='from')
        self.sync_value(self.factory.font_size, 'font_size', mode='from')
        self.sync_value(self.factory.bgcolor, 'bgcolor', mode='from')

        # self.sync_value(self.factory.text_width, 'text_width', mode='to')

        fmt = self.control.currentCharFormat()
        if self.factory.font_name:
            fmt.setFont(QFont(self.factory.font_name))

        #if self.factory.font_size:
        #    fmt.setFontPointSize(self.factory.font_size)
        self.control.setCurrentCharFormat(fmt)

    def _bgcolor_changed(self):
        p = QPalette()
        p.setColor(QPalette.Base, self.bgcolor)
        self.control.setPalette(p)

    def _font_size_changed(self):
        fmt = self.control.currentCharFormat()
        fmt.setFontPointSize(self.font_size)
        self.control.setCurrentCharFormat(fmt)


    def _refresh_fired(self):
        self.update_editor()

    def _clear_fired(self):
        if self.control:
            self.control.clear()

    def update_editor(self, *args, **kw):
        ctrl = self.control
        # print self.control.document().idealWidth()
        # print self.control.document().textWidth()
        # self.text_width=int(self.control.document().size().width())
        # print self.control.document().pageSize()
        # self.text_width=

        if self.value:
            while 1:
                try:
                    v, c, force = self.value.get(timeout=0.0001)
                except Empty:
                    return
                fmt = ctrl.currentCharFormat()
                fmt.setForeground(QColor(c))
                ctrl.setCurrentCharFormat(fmt)
                ctrl.appendPlainText(v)

                ctrl.moveCursor(QTextCursor.End)
                ctrl.ensureCursorVisible()


class DisplayEditor(BasicEditorFactory):
    klass = _DisplayEditor
    font_name = Str
    max_blocks = Int(0)

    #extended trait names
    bgcolor = Str
    font_size = Str
    clear = Str
    refresh = Str
    text_width = Str


class LoggerEditor(DisplayEditor):
    pass

#============= EOF =============================================
