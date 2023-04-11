# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import
from __future__ import print_function

# ============= standard library imports ========================
import os
import time
from datetime import datetime

from pyface.file_dialog import FileDialog
from pyface.tasks.api import Editor
from traits.api import (
    HasTraits,
    Property,
    Bool,
    Event,
    Unicode,
    List,
    String,
    Int,
    on_trait_change,
    Instance,
)

# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import add_extension, remove_extension
from pychron.pyscripts.context_editors.measurement_context_editor import (
    MeasurementContextEditor,
)
from pychron.pyscripts.tasks.gosub_popup_view import GosubPopupWidget
from pychron.pyscripts.tasks.widgets import myAdvancedCodeWidget

SCRIPT_PKGS = dict(
    Extraction="pychron.pyscripts.extraction_line_pyscript",
    Measurement="pychron.pyscripts.measurement_pyscript",
)


class Commands(HasTraits):
    script_commands = List
    command_objects = List

    def get_command(self, name):
        return next((ci for ci in self.script_commands if ci == name), None)

    def load_commands(self, kind):
        ps = self._pyscript_factory(kind)
        prepcommands = lambda cmds: [c[0] if isinstance(c, tuple) else c for c in cmds]

        self.script_commands = prepcommands(ps.get_commands())
        self.script_commands.sort()
        co = [self._command_factory(si) for si in self.script_commands]
        self.command_objects = co

    def _command_factory(self, scmd):
        cmd = None
        words = scmd.split("_")
        klass = "".join([w.capitalize() for w in words])

        pkg = "pychron.pyscripts.commands.api"
        cmd_name = "{}_command_editor".format(scmd)
        try:
            cmd = getattr(self, cmd_name)
        except AttributeError:
            m = __import__(pkg, globals={}, locals={}, fromlist=[klass])
            try:
                cmd = getattr(m, klass)()
                setattr(self, cmd_name, cmd)
            except AttributeError as e:
                if scmd:
                    print("exception", e)

        return cmd

    def _pyscript_factory(self, kind, **kw):
        klassname = "{}PyScript".format(kind)
        m = __import__(SCRIPT_PKGS[kind], fromlist=[klassname])
        klass = getattr(m, klassname)
        return klass(**kw)


class PyScriptEdit(HasTraits):
    text = ""
    path = ""
    context_editor = Instance(
        "pychron.pyscripts.context_editors.context_editor.ContextEditor"
    )
    _cached_text = ""

    def open_script(self, p):
        self.path = p
        with open(p, "r") as rfile:
            self.text = rfile.read()
        self.context_editor.load(self.get_text())

    def update_docstr(self):
        docstr = self.context_editor.generate_docstr()
        self._set_docstr(docstr)
        with open(self.path, "w") as wfile:
            wfile.write(self.get_text())

    def get_text(self):
        return self.text

    def set_text(self, s):
        self.text = s

    def _set_docstr(self, ds):
        to = list(self._remove_docstr())

        idx = 0
        if to[0].startswith("#!"):
            idx = 1

        for di in ds:
            to.insert(idx, di)

        to = "\n".join(to)
        self.set_text(to)
        self._cached_text = to

    def _remove_docstr(self):
        docstr_started = False
        check_docstr = True
        for i, t in enumerate(self.get_text().split("\n")):
            if check_docstr:
                if not docstr_started and t in ('"""', "'''"):
                    docstr_started = True
                    continue
                elif docstr_started:
                    if t in ('"""', "'''"):
                        check_docstr = False
                    continue

            yield t


class PyScriptEditor(Editor, PyScriptEdit):
    dirty = Bool(False)
    changed = Event
    show_line_numbers = Bool(True)
    path = Unicode
    name = Property(Unicode, depends_on="path")

    tooltip = Property(Unicode, depends_on="path")

    # context_editor = Any#Instance('pychron.pyscripts.context_editor.ContextEditor')

    suppress_change = False
    kind = String
    commands = Instance(Commands)

    auto_detab = Bool(True)
    highlight_line = Int
    trace_delay = Int  # ms
    gosub_event = String
    selected_command = String

    _no_update = False
    detectors = List
    isotopes = List

    def make_gosub(self):
        selection = self.control.code.textCursor().selectedText()
        dlg = FileDialog(action="save as", default_directory=os.path.dirname(self.path))

        p = None
        # root = os.path.dirname(self.path)
        # p = os.path.join(root, 'common', 'test_gosub.py')
        if dlg.open():
            p = dlg.path

        if p:
            p = add_extension(p, ".py")
            # p='/Users/ross/Desktop/foosub.py'
            with open(p, "w") as wfile:
                wfile.write("# Extracted Gosub\n")
                wfile.write("# Source: from {}\n".format(self.path))
                wfile.write(
                    "# Date: {}\n".format(datetime.now().strftime("%m-%d-%Y %H:%M"))
                )
                wfile.write("def main():\n")
                for li in selection.split("\u2029"):
                    wfile.write("    {}\n".format(li.lstrip()))

            p = remove_extension(p)
            rp = os.path.relpath(p, self.path)
            rp = rp.replace("/", ":")
            self.control.code.replace_selection("gosub('{}')".format(rp[3:]))

    def expand_gosub(self):
        def gen(text, yield_main=True):
            for li in text.split("\n"):
                sli = li.strip()
                if sli.startswith("gosub"):
                    yield "# ======== {} ==========".format(sli)

                    gosub = self._parse_gosub_line(sli)
                    gtext = self._get_gosub_text(gosub)
                    spaces = len(li) - len(li.lstrip())
                    nident = spaces - 4
                    ident = " " * nident
                    for gi in gen(gtext, False):
                        if gi.strip():
                            yield "{}{}".format(ident, gi)
                    yield "# ====================================================\n"
                else:
                    if not yield_main:
                        if li.startswith("def main"):
                            continue

                    yield li

        return "\n".join(gen(self.get_text()))

    def jump_to_gosub(self):
        name = self.get_active_gosub()
        self.gosub_event = name

    def get_scroll(self):
        return self.control.code.verticalScrollBar().value()

    def set_scroll(self, vp):
        return self.control.code.verticalScrollBar().setValue(vp)

    def _commands_default(self):
        cmd = Commands()
        cmd.load_commands(self.kind)
        return cmd

    def set_text(self, txt):
        if self.control:
            self.control.code.setPlainText(txt)

    def get_text(self):
        if self.control:
            return self.control.code.document().toPlainText()

    def create(self, parent):
        self.control = self._create_control(parent)

    def _create_control(self, parent):
        self.control = control = myAdvancedCodeWidget(parent, commands=self.commands)
        self._show_line_numbers_changed()

        # Connect signals for text changes.
        control.code.modificationChanged.connect(self._on_dirty_changed)
        control.code.textChanged.connect(self._on_text_changed)
        control.code.dclicked.connect(self._on_dclicked)
        control.code.modified_select.connect(self._on_modified_select)
        control.code.alt_select.connect(self._on_alt_select)

        # Load the editor's contents.
        self.load()

        return control

    def get_active_gosub(self):
        line = self.control.code.get_current_line()
        cmd = self._get_command(line)
        if cmd == "gosub":
            return self._parse_gosub_line(line)

    def _parse_gosub_line(self, line):
        if "," in line:
            line = line.split(",")[0]
            gosub = line[7:-1]
        else:
            gosub = line[7:-2]
        return gosub

    def insert_command(self, cmdobj):
        self.control.insert_command(cmdobj)

    @on_trait_change("context_editor:update_event")
    def handle_context_update(self):
        with no_update(self):
            docstr = self.context_editor.generate_docstr()
            self._set_docstr(docstr)
            self.dirty = True

    @on_trait_change("commands:command_objects:[+]")
    def handle_command_edit(self, obj, name, old, new):
        if old:
            self.control.code.replace_command(obj.to_string())

    def _get_command(self, line):
        cmd = line.split("(")[0]
        cmd = self.commands.get_command(cmd)
        return cmd

    def _on_alt_select(self, line, x, y):
        if line:
            cmd = self._get_command(line)
            if cmd == "gosub":
                gosub = self._parse_gosub_line(line)

                gtext = self._get_gosub_text(gosub)
                gsv = GosubPopupWidget(gtext)
                gsv.move(x, y)
                gsv.show()
                self.gsv = gsv
                self.control.code.popup = gsv

    def _get_gosub_text(self, gosub):
        root = os.path.dirname(self.path)
        new = gosub.replace("/", ":")
        new = add_extension(new, ".py")
        paths = new.split(":")
        p = os.path.join(root, *paths)
        if os.path.isfile(p):
            with open(p, "r") as rfile:
                return rfile.read()

    def _on_modified_select(self, line):
        if line:
            cmd = self._get_command(line)
            if cmd == "gosub":
                gosub = self._parse_gosub_line(line)
                self.gosub_event = gosub

    def _on_dclicked(self, line):
        if line:
            cmd = self._get_command(line)
            if cmd:
                self.selected_command = line
                self.control.highlight_line()
                # self.control.highlight_line(line)

    def _on_dirty_changed(self, dirty):
        if dirty:
            dirty = str(self.get_text()) != str(self._cached_text)

        self.dirty = dirty
        self._cached_text = self.get_text()

    def _on_text_changed(self):
        if str(self.get_text()) != str(self._cached_text):
            self.changed = True
            self.dirty = True
            self._cached_text = txt = self.get_text()
            if not self._no_update:
                if self.context_editor:
                    self.context_editor.load(txt)

    def _show_line_numbers_changed(self):
        if self.control is not None:
            self.control.code.line_number_widget.setVisible(self.show_line_numbers)
            self.control.code.update_line_number_width()

    def _highlight_line_changed(self):
        self.control.highlight_line(self.highlight_line)
        time.sleep(self.trace_delay * 0.001)

    def _get_tooltip(self):
        return self.path

    def _get_name(self):
        return os.path.basename(self.path) or "Untitled"

    # ===============================================================================
    # persistence
    # ===============================================================================
    def load(self, path=None):
        if path is None:
            path = self.path

        # We will have no path for a new script.
        if len(path) > 0:
            f = open(path, "r")
            text = f.read()
            f.close()
        else:
            text = ""

        if self.auto_detab:
            text = self._detab(text)
            self.save(path, text)
        self.control.code.setPlainText(text)

        if self.context_editor:
            self.context_editor.load(text)

        self._cached_text = text

        self.dirty = False

    def dump(self, path, txt=None):
        if txt is None:
            txt = self.get_text()
        if txt:
            with open(path, "w") as wfile:
                wfile.write(txt)

    save = dump

    def _detab(self, txt):
        return txt.replace("\t", " " * 4)


class MeasurementEditor(PyScriptEditor):
    kind = "Measurement"

    def _context_editor_default(self):
        return MeasurementContextEditor(
            available_detectors=self.detectors,
            isotopes=self.isotopes,
            valves=self.valves,
        )

        # def _editor_default(self):
        # return MeasurementParameterEditor(editor=self)


class ExtractionEditor(PyScriptEditor):
    kind = "Extraction"

    # def _editor_default(self):
    # return ParameterEditor(editor=self)


# ============= EOF =============================================
