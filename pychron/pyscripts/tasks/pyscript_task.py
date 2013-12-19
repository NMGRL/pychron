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
from traits.api import String, List, Instance, Any, \
    on_trait_change, Bool, Int
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter, Tabbed
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.editor_task import EditorTask
from pychron.helpers.filetools import add_extension
from pychron.pyscripts.tasks.pyscript_editor import ExtractionEditor, MeasurementEditor, \
    BakeoutEditor
from pychron.pyscripts.tasks.pyscript_panes import CommandsPane, DescriptionPane, \
    CommandEditorPane, ControlPane, ScriptBrowserPane
from pychron.paths import paths
from pychron.ui.preference_binding import bind_preference
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
import os
from pychron.execute_mixin import ExecuteMixin
from pychron.pyscripts.laser_pyscript import LaserPyScript



class PyScriptTask(EditorTask, ExecuteMixin):
    name = 'PyScript'
    kind = String
    kinds = List(['Extraction', 'Measurement'])
    commands_pane = Instance(CommandsPane)
    script_browser_pane = Instance(ScriptBrowserPane)

    wildcard = '*.py'
    _default_extension= '.py'

    auto_detab = Bool(True)
    _current_script = Any
    use_trace = Bool(False)
    trace_delay = Int(50)

    description=String

    def __init__(self, *args, **kw):
        super(PyScriptTask, self).__init__(*args, **kw)
        bind_preference(self, 'auto_detab', 'pychron.pyscript.auto_detab')

    def _runner_factory(self):
        # get the extraction line manager's mode
        man = self._get_el_manager()

        if man is None:
            self.warning_dialog('No Extraction line manager available')
            mode = 'normal'
        else:
            mode = man.mode

        if mode == 'client':
#            em = self.extraction_line_manager
            from pychron.initialization_parser import InitializationParser
            ip = InitializationParser()
            elm = ip.get_plugin('Experiment', category='general')
            runner = elm.find('runner')
            host, port, kind = None, None, None

            if runner is not None:
                comms = runner.find('communications')
                host = comms.find('host')
                port = comms.find('port')
                kind = comms.find('kind')

            if host is not None:
                host = host.text  # if host else 'localhost'
            if port is not None:
                port = int(port.text)  # if port else 1061
            if kind is not None:
                kind = kind.text  # if kind else 'udp'

            from pychron.pyscripts.pyscript_runner import RemotePyScriptRunner
            runner = RemotePyScriptRunner(host, port, kind)
        else:
            from pychron.pyscripts.pyscript_runner import PyScriptRunner
            runner = PyScriptRunner()

        return runner

    def _get_el_manager(self):
        app = self.window.application
        man = app.get_service('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')
        return man

    def _do_execute(self):
        self.debug('do execute')

        self._current_script = None
        ae = self.active_editor
        if isinstance(ae, ExtractionEditor):
            root, fn = os.path.split(ae.path)
            kind = self._extract_kind(ae.path)
            klass = ExtractionPyScript
            if kind == 'Laser':
                klass = LaserPyScript

            script = klass(
                            application=self.window.application,
                            root=root,
                            name=fn,
                            runner=self._runner)

            if script.bootstrap():
                script.set_default_context()
                try:
                    script.test()
                except Exception, e:
                    return
                self._current_script = script
                script.setup_context(extract_device='fusions_diode')
                if self.use_trace:
                    self.active_editor.trace_delay = self.trace_delay

                t = script.execute(trace=self.use_trace)

        self.executing = False

    def _start_execute(self):
        self.debug('start execute')

        # make a script runner
        self._runner = None
        runner = self._runner_factory()
        if runner is None:
            return
        else:
            self._runner = runner
            return True

    def _cancel_execute(self):
        self.debug('cancel execute')
        if self._current_script:
            self._current_script.cancel()

    def _default_directory_default(self):
        return paths.scripts_dir

    def create_dock_panes(self):
        self.commands_pane = CommandsPane()
        self.command_editor_pane = CommandEditorPane()
        # self.editor_pane = EditorPane()
        self.control_pane = ControlPane(model=self)
        self.script_browser_pane=ScriptBrowserPane()

        return [
                self.commands_pane,
                self.command_editor_pane,
                # self.editor_pane,
                self.control_pane,
                DescriptionPane(model=self),
                self.script_browser_pane
                ]

    def _save_file(self, path):
        self.active_editor.dump(path)
        return True

    def find(self):
        if self.active_editor:
            self.active_editor.control.enable_find()

    def replace(self):
        if self.active_editor:
            self.active_editor.control.enable_replace()

    def new(self):

        # todo ask for script type
        info = self.edit_traits(view='kind_select_view')
        if info.result:
            self._open_editor(path='')
            return True

    def _open_file(self, path, **kw):
        self.info('opening pyscript: {}'.format(path))
        self._open_editor(path, **kw)

    def _extract_kind(self, path):
        with open(path, 'r') as fp:
            for line in fp:
                if line.startswith('#!'):
                    return line.strip()[2:]

    def _open_editor(self, path, kind=None):
        if path:
            kind = self._extract_kind(path)

        if kind == 'Measurement':
            klass = MeasurementEditor
        elif kind == 'Bakeout':
            klass = BakeoutEditor
        else:
            klass = ExtractionEditor

        editor = klass(path=path,
                       auto_detab=self.auto_detab)

        super(PyScriptTask, self)._open_editor(editor)

    @on_trait_change('commands_pane:command_object')
    def _update_selected(self, new):
        self.command_editor_pane.command_object = new
        if new:
            self.description = new.description

    def _active_editor_changed(self):
        if self.active_editor:
            self.commands_pane.name = self.active_editor.kind

            self.commands_pane.command_objects = self.active_editor.commands.command_objects
            self.commands_pane.commands = self.active_editor.commands.script_commands

            self.script_browser_pane.root=os.path.dirname(self.active_editor.path)
            # self.editor_pane.editor = self.active_editor.editor

    @on_trait_change('_current_script:trace_line')
    def _handle_lineno(self, new):
        self.active_editor.highlight_line = new

    @on_trait_change('script_browser_pane:dclicked')
    def _handle_selected_file(self):
        new=self.script_browser_pane.selected
        self.debug('selected file {}'.format(new))
        root=self.script_browser_pane.root
        self._open_pyscipt(new, root)

    @on_trait_change('active_editor:selected_gosub')
    def _handle_selected_gosub(self, new):

        self.debug('selected gosub {}'.format(new))
        if new:
            root=os.path.dirname(self.active_editor.path)
            self._open_pyscipt(new, root)
            # self.active_editor.trait_set(selected_gosub='', trait_change_notify=False)

    @on_trait_change('active_editor:selected_command')
    def _handle_selected_command(self, new):
        self.debug('selected command {}'.format(new))
        if new:
            self.commands_pane.set_command(new)

    def _open_pyscipt(self, new, root):
        new = new.replace('/', ':')
        new = add_extension(new, '.py')
        paths = new.split(':')

        for editor in self.editor_area.editors:
            if editor.name==paths[-1]:
                self.activate_editor(editor)
                break
        else:
            p=os.path.join(root, *paths)

            if os.path.isfile(p):
                self._open_file(p)
            else:
                self.warning_dialog('File does not exist {}'.format(p))

    def _get_example(self):
        if self.selected:
            return self.selected.example
        return ''

    def _default_layout_default(self):
        left=Splitter(Tabbed(PaneItem('pychron.pyscript.commands', height=500, width=125),
                             PaneItem('pychron.pyscript.script_browser')),
                      PaneItem('pychron.pyscript.commands_editor', height=200, width=125),
                      orientation='vertical')
        bottom=PaneItem('pychron.pyscript.description')
        return TaskLayout(id='pychron.pyscript',
                          left=left,
                          bottom=bottom
                          )


        #============= EOF =============================================
