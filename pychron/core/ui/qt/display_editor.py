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
from Queue import Empty

from pyface.qt.QtGui import QPlainTextEdit, QTextCursor, QPalette, QColor, QFont
from traits.api import Color, Str, Event, Int
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


# ============= standard library imports ========================
# ============= local library imports  ==========================


class _DisplayEditor(Editor):
    clear = Event
    refresh = Event
    control_klass = QPlainTextEdit
    font_size = Int
    bgcolor = Color
    text_width = Int
    _nominal_character_width = None

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

    # def _font_size_changed(self):
    #     print 'asdfasdf', self.font_size
        # fmt = self.control.currentCharFormat()
        # fmt.setFontPointSize(self.font_size)
        # self.control.setCurrentCharFormat(fmt)

    def _refresh_fired(self):
        self.update_editor()

    def _clear_fired(self):
        if self.control:
            self.control.clear()

    def _calculate_nominal_character_width(self, v, ctrl):
        fm = ctrl.fontMetrics()
        br = fm.boundingRect
        width = ctrl.width()
        i = 0
        while 1:
            if br(v * i).width() > width:
                break
            i += 1
        self._nominal_character_width = i - 3

    def _check_character_width(self, v, ctrl):
        fm = ctrl.fontMetrics()
        br = fm.boundingRect
        width = ctrl.width()
        return br(v).width() > width

    def update_editor(self, *args, **kw):
        ctrl = self.control
        if self.value:
            while 1:
                try:
                    v, c, force, is_marker = self.value.get(timeout=0.01)
                except Empty:
                    return
                fmt = ctrl.currentCharFormat()
                fmt.setForeground(QColor(c))
                fmt.setFontPointSize(self.font_size)
                ctrl.setCurrentCharFormat(fmt)

                if is_marker:
                    ov = v
                    if self._nominal_character_width is None:
                        self._calculate_nominal_character_width(ov, ctrl)
                    v = ov * self._nominal_character_width

                    if self._check_character_width(v, ctrl):
                        self._calculate_nominal_character_width(ov, ctrl)
                        v = ov * self._nominal_character_width

                ctrl.appendPlainText(v)

                ctrl.moveCursor(QTextCursor.End)
                ctrl.ensureCursorVisible()


class DisplayEditor(BasicEditorFactory):
    klass = _DisplayEditor
    font_name = Str
    max_blocks = Int(50)

    #extended trait names
    bgcolor = Str
    font_size = Str
    clear = Str
    refresh = Str
    text_width = Str


class LoggerEditor(DisplayEditor):
    pass

# ============= EOF =============================================
