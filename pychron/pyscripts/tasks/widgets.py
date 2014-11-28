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

#============= enthought library imports =======================
from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from PySide.QtGui import QTextCursor, QTextEdit, QTextFormat, QCursor, QApplication, QTextCharFormat
from pyface.ui.qt4.code_editor.code_widget import AdvancedCodeWidget, CodeWidget
from pyface.ui.qt4.code_editor.find_widget import FindWidget
from pyface.ui.qt4.code_editor.replace_widget import ReplaceWidget

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pyscripts.tasks.pyscript_lexer import PyScriptLexer


class myCodeWidget(CodeWidget):
    dclicked = QtCore.Signal((str,))
    modified_select = QtCore.Signal((str,))
    _current_pos = None
    gotos = ['gosub']

    def keyPressEvent(self, event):
        super(myCodeWidget, self).keyPressEvent(event)

        if event.modifiers() & Qt.ControlModifier:
            QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
            # self.setMouseTracking(True)

    def keyReleaseEvent(self, event):
        super(myCodeWidget, self).keyReleaseEvent(event)
        # self.setMouseTracking(False)
        QApplication.restoreOverrideCursor()

    def clear_selected(self):
        # self.setMouseTracking(False)
        self.clear_underline()
        QApplication.restoreOverrideCursor()

    def clear_underline(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        fmt = cursor.charFormat()
        fmt.setFontUnderline(False)
        cursor.beginEditBlock()
        cursor.setCharFormat(fmt)
        cursor.endEditBlock()

    def mouseMoveEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.clear_underline()
            cursor, line = self._get_line_cursor(event.pos())

            for goto in self.gotos:
                if line.strip().startswith(goto):
                    fmt = QTextCharFormat()
                    fmt.setFontUnderline(True)
                    fmt.setUnderlineStyle(QTextCharFormat.WaveUnderline)
                    fmt.setUnderlineColor(QtGui.QColor('blue'))
                    # cursor.clearSelection()
                    cursor.select(QTextCursor.BlockUnderCursor)

                    cursor.beginEditBlock()
                    cursor.setCharFormat(fmt)
                    cursor.endEditBlock()

                    break

        super(myCodeWidget, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            cursor, line = self._get_line_cursor(event.pos())
            self.modified_select.emit(line.strip())
            self.clear_selected()

        self._current_pos = None
        super(myCodeWidget, self).mousePressEvent(event)

    def get_current_line(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        return line.strip()

    def _get_line_cursor(self, pos):
        cursor = self.cursorForPosition(pos)
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        return cursor, line


    def mouseDoubleClickEvent(self, event):
        self.clear_selected()

        self._current_pos = event.pos()
        cursor, line = self._get_line_cursor(self._current_pos)
        self.dclicked.emit(line.strip())


    def replace_command(self, cmd):
        if self._current_pos:
            cursor, line = self._get_line_cursor(self._current_pos)
            lead = len(line) - len(line.lstrip())
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText('{}{}'.format(' ' * lead, cmd))
            cursor.endEditBlock()


class myAdvancedCodeWidget(AdvancedCodeWidget):
    commands = None

    def __init__(self, parent, commands=None, font=None):
        QtGui.QWidget.__init__(self, parent)

        self.setAcceptDrops(True)
        self.commands = commands
        self.code = myCodeWidget(self, font=font)

        #set lexer manually instead of by name
        lexer = PyScriptLexer(commands)
        self.code.highlighter._lexer = lexer
        self.code.setMouseTracking(True)

        #AdvanceCodeWidget
        #=====================================
        self.find = FindWidget(self)
        self.find.hide()
        self.replace = ReplaceWidget(self)
        self.replace.hide()
        self.replace.replace_button.setEnabled(False)
        self.replace.replace_all_button.setEnabled(False)

        self.active_find_widget = None
        self.previous_find_widget = None

        self.code.selectionChanged.connect(self._update_replace_enabled)

        self.find.line_edit.returnPressed.connect(self.find_next)
        self.find.next_button.clicked.connect(self.find_next)
        self.find.prev_button.clicked.connect(self.find_prev)

        self.replace.line_edit.returnPressed.connect(self.find_next)
        self.replace.line_edit.textChanged.connect(
            self._update_replace_all_enabled)
        self.replace.next_button.clicked.connect(self.find_next)
        self.replace.prev_button.clicked.connect(self.find_prev)
        self.replace.replace_button.clicked.connect(self.replace_next)
        self.replace.replace_all_button.clicked.connect(self.replace_all)

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.code)
        layout.addWidget(self.find)
        layout.addWidget(self.replace)

        self.setLayout(layout)

        self.edit_color = QtGui.QColor('blue').lighter(175)
        #=====================================

    def insert_command(self, cmd):
        cur = self.code.textCursor()
        self._insert_command(cmd, cur)

    def _insert_command(self, cmd, cur):
        text = cmd.to_string()
        if text:
            # get the indent level of the line
            # if line starts with a special keyword add indent

            block = cur.block()
            line = block.text()
            indent = max(4, self.code._get_indent_position(line))
            line = line.strip()
            token = line.split(' ')[0]
            token = token.strip()

            if token in ('if', 'for', 'while', 'with', 'def', 'class'):
                indent += 4

            indent = ' ' * indent
            cur.movePosition(QTextCursor.EndOfLine)
            cur.insertText('\n{}{}'.format(indent, text))

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('traits-ui-tabular-editor'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        mime = e.mimeData()
        data = mime.data('traits-ui-tabular-editor')
        idx = int(data.split(' ')[1])
        #        cmd = ''
        cmd = self.commands.command_objects[idx]
        if cmd:
            cur = self.code.cursorForPosition(e.pos())
            self._insert_command(cmd, cur)

    def highlight_line(self, lineno=None):
        if lineno is None:
            color = self.edit_color
        else:
            color = self.code.line_highlight_color

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(color)
        selection.format.setProperty(
            QTextFormat.FullWidthSelection, True)

        selection.cursor = self.code.textCursor()
        if lineno is not None:
            doc = self.code.document()
            block = doc.findBlockByLineNumber(lineno - 1)
            pos = block.position()
            selection.cursor.setPosition(pos)
            selection.cursor.clearSelection()
        self.code.setExtraSelections([selection])

# ============= EOF =============================================

