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
    Unicode, List, String, Int, on_trait_change, Instance
from pyface.tasks.api import Editor

# from pyface.ui.qt4.python_editor import PythonEditorEventFilter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pyscripts.tasks.widgets import myAdvancedCodeWidget

SCRIPT_PKGS = dict(Extraction='pychron.pyscripts.extraction_line_pyscript',
                   Measurement='pychron.pyscripts.measurement_pyscript')


class Commands(HasTraits):
    script_commands = List
    command_objects = List

    def get_command(self, name):
        return next((ci for ci in self.script_commands if ci==name), None)

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
    # editor = Any
    suppress_change = False
    kind = String
    commands = Instance(Commands)

    auto_detab = Bool(True)
    highlight_line = Int
    trace_delay = Int  # ms
    selected_gosub=String
    selected_command=String
    _cached_text=''

    def get_scroll(self):
        return self.control.code.verticalScrollBar().value()

    def set_scroll(self, vp):
        return self.control.code.verticalScrollBar().setValue(vp)

    def _commands_default(self):
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

        self.control = control = myAdvancedCodeWidget(parent,
                                              commands=self.commands)
        self._show_line_numbers_changed()

        # Connect signals for text changes.
        control.code.modificationChanged.connect(self._on_dirty_changed)
        control.code.textChanged.connect(self._on_text_changed)
        control.code.dclicked.connect(self._on_dclicked)
        control.code.modified_select.connect(self._on_modified_select)
        # Load the editor's contents.
        self.load()

        return control

    def get_active_gosub(self):
        line=self.control.code.get_current_line()
        cmd = self._get_command(line)
        if cmd == 'gosub':
            return line[7:-2]

    @on_trait_change('commands:command_objects:[+]')
    def handle_command_edit(self, obj, name, old, new):
        if old:
            self.control.code.replace_command(obj.to_string())

    def _get_command(self, line):
        cmd = line.split('(')[0]
        cmd = self.commands.get_command(cmd)
        return cmd

    def _on_modified_select(self, line):
        if line:
            cmd=self._get_command(line)
            if cmd=='gosub':
                self.selected_gosub=line[7:-2]
                self.selected_gosub=''

    def _on_dclicked(self, line):
        if line:
            cmd=self._get_command(line)
            if cmd:
                self.selected_command=line

    def _on_dirty_changed(self, dirty):
        if dirty:
            dirty=str(self.getText()) != str(self._cached_text)

        self.dirty = dirty
        self._cached_text = self.getText()

    def _on_text_changed(self):
        # print len(self.getText()), len(self._cached_text)
        if str(self.getText()) !=str(self._cached_text):
            # print self.getText()
            # print self._cached_text
    #        if not self.suppress_change:
    #     self.editor.parse(self.getText())
            self.changed = True
            self.dirty = True
            self._cached_text=self.getText()

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
        self._cached_text=text

    def dump(self, path, txt=None):
        if txt is None:
            txt = self.getText()
        if txt:
            with open(path, 'w') as fp:
                fp.write(txt)

    save = dump

    def _detab(self, txt):
        return txt.replace('\t', ' ' * 4)


class MeasurementEditor(PyScriptEditor):
    kind = 'Measurement'

    # def _editor_default(self):
    #     return MeasurementParameterEditor(editor=self)


class ExtractionEditor(PyScriptEditor):
    kind = 'Extraction'

    # def _editor_default(self):
    #     return ParameterEditor(editor=self)

#============= EOF =============================================
