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
import os
import time

from traits.api import HasTraits, Property, Bool, Event, \
    Unicode, Any, List, String, cached_property, Int
from pyface.tasks.api import Editor
from PySide.QtGui import QTextCursor, QTextFormat, QTextEdit

from pychron.pyscripts.parameter_editor import MeasurementParameterEditor, \
    ParameterEditor

# from pyface.ui.qt4.python_editor import PythonEditorEventFilter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pyscripts.tasks.pyscript_lexer import PyScriptLexer

SCRIPT_PKGS = dict(Bakeout='pychron.pyscripts.bakeout_pyscript',
                   Extraction='pychron.pyscripts.extraction_line_pyscript',
                   Measurement='pychron.pyscripts.measurement_pyscript'
)

from pyface.ui.qt4.code_editor.code_widget import AdvancedCodeWidget


class myCodeWidget(AdvancedCodeWidget):
    commands = None
    on_selected_gosub=None

    def __init__(self, parent, commands=None, *args, **kw):
        super(myCodeWidget, self).__init__(parent, *args, **kw)
        self.commands = commands
        self.setAcceptDrops(True)

        #setup lexer
        lexer = PyScriptLexer(commands)
        self.code.highlighter._lexer = lexer

        self.code.mouseDoubleClickEvent=self.mouseDoubleClickEvent
        # self.code.mouseMoveEvent=self.mouseMoveEvent
        # self.code.keyPressEvent=self.keyPressEvent
        # self.code.keyReleaseEvent=self.keyReleaseEvent

        self.code.setMouseTracking(True)

    # def enterEvent(self, e):
    #     # self.grabMouse()
    #
    # def leaveEvent(self, e):
    #     # self.releaseMouse()
    def mouseDoubleClickEvent(self, event):
        if self.on_selected_gosub:
            cur = self.code.cursorForPosition(event.pos())
            line=self._over_gosub(event, cur)
            if line:
                self.on_selected_gosub(line.strip())

    def _over_gosub(self, event, cursor):
        # if event.modifiers() & QtCore.Qt.ControlModifier:

        cursor.select(QTextCursor.WordUnderCursor)
        if cursor.selectedText() == 'gosub':
            self.code.setTextCursor(cursor)

            cursor.select(QTextCursor.LineUnderCursor)
            line = cursor.selectedText()
            # self.code.setCursor(QCursor(Qt.ArrowCursor))
            # QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            return line
        # else:
        #     self.code.setCursor(QCursor(Qt.IBeamCursor))
            # QApplication.restoreOverrideCursor()

    # def keyPressEvent(self, event):
    #     super(myCodeWidget, self).keyPressEvent(event)
    #     cur = self.code.textCursor()
    #     self._over_gosub(event, cur)
    #
    # def keyReleaseEvent(self, event):
    #     print 'release'
    #     super(myCodeWidget, self).keyReleaseEvent(event)
    #     cur=self.code.textCursor()
    #     self._over_gosub(event,cur)
    #
    # def mouseMoveEvent(self, event):
    #     cur= self.code.cursorForPosition(event.pos())
    #     self._over_gosub(event, cur)


    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('traits-ui-tabular-editor'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        mime = e.mimeData()
        idx = mime.data('traits-ui-tabular-editor')

        #        cmd = ''
        cmd = self.commands.command_objects[int(idx)]
        if cmd:
            text = cmd.to_string()
            if text:
                cur = self.code.cursorForPosition(e.pos())

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

    def highlight_line(self, lineno):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(self.code.line_highlight_color)
        selection.format.setProperty(
            QTextFormat.FullWidthSelection, True)

        doc = self.code.document()
        block = doc.findBlockByLineNumber(lineno - 1)
        pos = block.position()
        selection.cursor = self.code.textCursor()
        selection.cursor.setPosition(pos)
        selection.cursor.clearSelection()
        self.code.setExtraSelections([selection])


class Commands(HasTraits):
    script_commands = List
    command_objects = List

    def load_commands(self, kind):
        ps = self._pyscript_factory(kind)
        prepcommands = lambda cmds: [c[0] if isinstance(c, tuple) else c for c in cmds]

        self.script_commands = prepcommands(ps.get_commands())
        self.script_commands.sort()
        co = [self._command_factory(si)
              for si in self.script_commands]
        self.command_objects = co

    def _command_factory(self, scmd):

        cmd = None
        words = scmd.split('_')
        klass = ''.join(map(str.capitalize, words))

        pkg = 'pychron.pyscripts.commands.api'
        cmd_name = '{}_command_editor'.format(scmd)
        try:
            cmd = getattr(self, cmd_name)
        except AttributeError:

            m = __import__(pkg, globals={}, locals={}, fromlist=[klass])
            try:
                cmd = getattr(m, klass)()
                setattr(self, cmd_name, cmd)
            except AttributeError, e:
                if scmd:
                    print e

        return cmd

    def _pyscript_factory(self, kind, **kw):

        klassname = '{}PyScript'.format(kind)
        m = __import__(SCRIPT_PKGS[kind], fromlist=[klassname])
        klass = getattr(m, klassname)
        return klass(**kw)


class PyScriptEditor(Editor):
    dirty = Bool(False)
    changed = Event
    show_line_numbers = Bool(True)
    path = Unicode
    name = Property(Unicode, depends_on='path')

    tooltip = Property(Unicode, depends_on='path')
    editor = Any
    suppress_change = False
    kind = String
    commands = Property(depends_on='kind')

    auto_detab = Bool(True)
    highlight_line = Int
    trace_delay = Int  # ms
    selected_gosub=String

    def get_scroll(self):
        return self.control.code.verticalScrollBar().value()

    def set_scroll(self, vp):
        return self.control.code.verticalScrollBar().setValue(vp)

    @cached_property
    def _get_commands(self):
        if self.kind:
            cmd = Commands()
            cmd.load_commands(self.kind)
            return cmd

    def setText(self, txt):
        if self.control:
            self.control.code.setPlainText(txt)

    def getText(self):
        if self.control:
            return self.control.code.document().toPlainText()

    def create(self, parent):
        self.control = self._create_control(parent)

    def _create_control(self, parent):

        self.control = control = myCodeWidget(parent,
                                              commands=self.commands)
        #        self.control = control = AdvancedCodeWidget(parent)
        self._show_line_numbers_changed()

        # Install event filter to trap key presses.
        #        event_filter = PythonEditorEventFilter(self, self.control)
        #        event_filter.control = self.control
        #        self.control.installEventFilter(event_filter)
        #        self.control.code.installEventFilter(event_filter)

        # Connect signals for text changes.
        control.code.modificationChanged.connect(self._on_dirty_changed)
        control.code.textChanged.connect(self._on_text_changed)

        # Load the editor's contents.
        self.load()

        control.on_selected_gosub=self._on_selected_gosub

        return control

    def _on_selected_gosub(self, gs):
        self.selected_gosub=gs

    def _on_dirty_changed(self, dirty):
        self.dirty = dirty

    def _on_text_changed(self):
    #        if not self.suppress_change:
        self.editor.parse(self.getText())
        self.changed = True
        self.dirty = True

    #    @on_trait_change('editor:body')
    #    def _on_body_change(self):
    #        if self.editor.body:
    #            self.suppress_change = True
    #            self.setText(self.editor.body)
    #            self.suppress_change = False

    def _show_line_numbers_changed(self):
        if self.control is not None:
            self.control.code.line_number_widget.setVisible(
                self.show_line_numbers)
            self.control.code.update_line_number_width()

    def _highlight_line_changed(self):
        self.control.highlight_line(self.highlight_line)
        time.sleep(self.trace_delay * 0.001)

    def _get_tooltip(self):
        return self.path

    def _get_name(self):
        return os.path.basename(self.path) or 'Untitled'

    #===============================================================================
    # persistence
    #===============================================================================
    def load(self, path=None):
        if path is None:
            path = self.path

        # We will have no path for a new script.
        if len(path) > 0:
            f = open(self.path, 'r')
            text = f.read()
            f.close()
        else:
            text = ''

        if self.auto_detab:
            text = self._detab(text)
            self.save(path, text)
        self.control.code.setPlainText(text)

        self.dirty = False

    def dump(self, path, txt=None):
        if txt is None:
            txt = self.getText()
        if txt:
            with open(path, 'w') as fp:
                fp.write(txt)

    save = dump
    #    def save(self, path):
    #        self.dump(path)
    def _detab(self, txt):
        return txt.replace('\t', ' ' * 4)


class MeasurementEditor(PyScriptEditor):
#    editor = Instance(MeasurementParameterEditor, ())
    kind = 'Measurement'

    def _editor_default(self):
        return MeasurementParameterEditor(editor=self)


class ExtractionEditor(PyScriptEditor):
#    editor = Instance(ParameterEditor, ())
    kind = 'Extraction'

    def _editor_default(self):
        return ParameterEditor(editor=self)


class BakeoutEditor(PyScriptEditor):
    kind = 'Bakeout'

    def _editor_default(self):
        return ParameterEditor(editor=self)

#============= EOF =============================================
