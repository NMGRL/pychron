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
from pyface.tasks.action.schema import SToolBar
from traits.api import String, List, Instance, Any, \
    on_trait_change, Bool, Int
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter, Tabbed
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.envisage.tasks.editor_task import EditorTask
from pychron.core.helpers.filetools import add_extension
from pychron.pyscripts.tasks.git_actions import CommitChangesAction
from pychron.pyscripts.tasks.pyscript_actions import JumpToGosubAction, ExpandGosubsAction, MakeGosubAction
from pychron.pyscripts.tasks.pyscript_editor import ExtractionEditor, MeasurementEditor, PyScriptEditor
from pychron.pyscripts.tasks.pyscript_panes import CommandsPane, DescriptionPane, \
    CommandEditorPane, ControlPane, ScriptBrowserPane, ContextEditorPane, RepoPane
from pychron.paths import paths
from pychron.execute_mixin import ExecuteMixin


class PyScriptTask(EditorTask, ExecuteMixin):
    id = 'pychron.pyscript.task'
    name = 'PyScript'
    kind = String
    kinds = List(['Extraction', 'Measurement'])
    commands_pane = Instance(CommandsPane)
    script_browser_pane = Instance(ScriptBrowserPane)
    command_editor_pane = Instance(CommandEditorPane)
    context_editor_pane = Instance(ContextEditorPane)

    repo_manager = Instance('pychron.git_archive.repo_manager.GitRepoManager')
    repo_pane = None

    wildcard = '*.py'
    _default_extension = '.py'

    auto_detab = Bool(True)
    _current_script = Any
    use_trace = Bool(False)
    trace_delay = Int(50)

    description = String

    tool_bars = [SToolBar(JumpToGosubAction(), ExpandGosubsAction(),
                          MakeGosubAction()), ]

    use_git_repo = Bool

    _on_close = None
    _on_save_as = None

    def __init__(self, *args, **kw):
        super(PyScriptTask, self).__init__(*args, **kw)
        self.bind_preferences()

        if self.use_git_repo:
            if not next((ti for ti in self.tool_bars if ti.id == 'pychron.pyscript.git_toolbar'), None):
                self.tool_bars.append(SToolBar(CommitChangesAction(),
                                               name='pychron.pyscript.git_toolbar'))

    def set_on_close_handler(self, func):
        self._on_close = func

    def set_on_save_as_handler(self, func):
        self._on_save_as = func

    def commit_changes(self):
        self.repo_manager.commit_dialog()
        if self.active_editor:
            self.repo_manager.load_file_history(self.active_editor.path)

    def make_gosub(self):
        editor = self.has_active_editor()
        if editor:
            editor.make_gosub()

    def expand_gosubs(self):
        editor = self.has_active_editor()
        if editor:
            text = editor.expand_gosub()
            editor = editor.__class__()
            if self.editor_area:
                self.editor_area.add_editor(editor)
                self.editor_area.activate_editor(editor)
                editor.set_text(text)

    def jump_to_gosub(self):
        editor = self.has_active_editor()
        if editor:
            editor.jump_to_gosub()

        # root = os.path.dirname(self.active_editor.path)
        # name = self.active_editor.get_active_gosub()
        # if name:
        #     self._open_pyscript(name, root)

    def execute_script(self, *args, **kw):
        return self._do_execute(*args, **kw)

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

    #task protocol
    def activated(self):
        super(PyScriptTask, self).activated()

        self._use_git_repo_changed(self.use_git_repo)

    def bind_preferences(self):
        self._preference_binder('pychron.pyscript', ('auto_detab', 'use_git_repo'))
        if self.use_git_repo:
            self._preference_binder('pychron.pyscript',('remote',), obj=self.repo_manager)

    def create_dock_panes(self):
        self.commands_pane = CommandsPane()
        self.command_editor_pane = CommandEditorPane()
        self.control_pane = ControlPane(model=self)
        self.script_browser_pane = ScriptBrowserPane()
        self.context_editor_pane = ContextEditorPane()
        panes = [
            self.commands_pane,
            self.command_editor_pane,
            self.control_pane,
            DescriptionPane(model=self),
            self.script_browser_pane,
            self.context_editor_pane]
        if self.use_git_repo:
            self.repo_pane = RepoPane(model=self.repo_manager)
            self.repo_manager.on_trait_change(self._handle_path_change, 'path_dirty')
            panes.append(self.repo_pane)
        return panes

    def save_as(self):
        if super(PyScriptTask, self).save_as():
            if self._on_save_as:
                self._on_save_as()

    #private
    def _prompt_for_save(self):
        ret = super(PyScriptTask, self)._prompt_for_save()
        if self.use_git_repo:
            #check for uncommitted changes
            if self.repo_manager.has_staged():
                return self.repo_manager.commit_dialog()
        if ret:
            if self._on_close:
                self._on_close()

        return ret

    def _do_execute(self, name=None, root=None, kind='Extraction', **kw):
        self._start_execute()

        self.debug('do execute')

        self._current_script = None

        if not (name and root and kind):
            ae = self.active_editor
            if isinstance(ae, ExtractionEditor):
                root, name = os.path.split(ae.path)
                kind = self._extract_kind(ae.path)

        if name and root and kind:
            ret = self._execute_extraction(name, root, kind, **kw)
            self.executing = False
            return ret

    def _execute_extraction(self, name, root, kind, new_thread=True,
                            delay_start=0,
                            on_completion=None,
                            context=None):
        from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript

        klass = ExtractionPyScript
        if kind == 'Laser':
            from pychron.pyscripts.laser_pyscript import LaserPyScript

            klass = LaserPyScript

        script = klass(application=self.application,
                       root=root,
                       name=add_extension(name, '.py'),
                       runner=self._runner)

        if script.bootstrap():
            if context:
                script.setup_context(**context)
            else:
                script.set_default_context()
            try:
                script.test()
            except Exception, e:
                return
            self._current_script = script
            script.setup_context(extract_device='fusions_diode')
            if self.use_trace:
                self.active_editor.trace_delay = self.trace_delay

            ret = script.execute(trace=self.use_trace, new_thread=new_thread, delay_start=delay_start,
                                 on_completion=on_completion)
            return not script.is_canceled() and ret

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

    def _save_file(self, path):
        self.active_editor.dump(path)
        if self.use_git_repo:
            self.repo_manager.add(path, commit=False)

        return True

    def _open_file(self, path, **kw):
        self.info('opening pyscript: {}'.format(path))
        return self._open_editor(path, **kw)

    def _extract_kind(self, path):
        with open(path, 'r') as rfile:
            for line in rfile:
                if line.startswith('#!'):
                    return line.strip()[2:]

    def _open_editor(self, path, kind=None):
        if path:
            kind = self._extract_kind(path)

        if kind == 'Measurement':
            klass = MeasurementEditor
        else:
            klass = ExtractionEditor

        dets, isotopes, valves = [], [], []
        man = self.application.get_service('pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager')
        if man:
            dets = [di.name for di in man.spectrometer.detectors]
            isotopes = man.spectrometer.isotopes
        man = self.application.get_service('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')
        if man:
            valves = man.get_valve_names()

        editor = klass(path=path,
                       auto_detab=self.auto_detab,
                       valves=valves,
                       isotopes=isotopes,
                       detectors=dets)

        super(PyScriptTask, self)._open_editor(editor)
        return True

    def _open_pyscript(self, new, root):
        new = new.replace('/', ':')
        new = add_extension(new, '.py')
        paths = new.split(':')

        for editor in self.editor_area.editors:
            if editor.name == paths[-1]:
                self.activate_editor(editor)
                break
        else:
            p = os.path.join(root, *paths)

            if os.path.isfile(p):
                self._open_file(p)
            else:
                self.warning_dialog('File does not exist {}'.format(p))

    def _get_example(self):
        if self.selected:
            return self.selected.example
        return ''

    #handlers
    def _handle_path_change(self, new):
        self.debug('path changed {}'.format(new))
        for ei in self.editor_area.editors:
            if ei.path == new:
                ei.load()

    def _use_git_repo_changed(self, new):
        self.debug('use git repo changed {}'.format(new))
        if new:
            self.debug('initialize git repo at {}'.format(paths.scripts_dir))
            if self.repo_manager.init_repo(paths.scripts_dir):
                pass
                # self.repo_manager.add_unstaged(None, extension='.py', use_diff=True)
            else:
                for p in (paths.measurement_dir, paths.extraction_dir,
                          paths.post_equilibration_dir, paths.post_measurement_dir):
                    self.debug('add unstaged files from {}'.format(p))
                    self.repo_manager.add_unstaged(p, extension='.py', use_diff=False)

                self.debug('committing unstaged pyscripts')
                self.repo_manager.commit('auto added unstaged pyscripts')

    def _active_editor_changed(self):
        if self.active_editor:
            self.commands_pane.name = self.active_editor.kind

            self.commands_pane.command_objects = self.active_editor.commands.command_objects
            self.commands_pane.commands = self.active_editor.commands.script_commands

            self.script_browser_pane.root = os.path.dirname(self.active_editor.path)
            self.context_editor_pane.editor = self.active_editor.context_editor

            if self.use_git_repo:
                self.repo_manager.selected = self.active_editor.path

    @on_trait_change('command_editor_pane:insert_button')
    def _insert_fired(self):
        self.active_editor.insert_command(self.command_editor_pane.command_object)

    @on_trait_change('commands_pane:command_object')
    def _update_selected(self, new):
        self.command_editor_pane.command_object = new
        if new:
            self.description = new.description

    @on_trait_change('_current_script:trace_line')
    def _handle_lineno(self, new):
        self.active_editor.highlight_line = new

    @on_trait_change('script_browser_pane:dclicked')
    def _handle_selected_file(self):
        new = self.script_browser_pane.selected
        self.debug('selected file {}'.format(new))
        root = self.script_browser_pane.root
        self._open_pyscript(new, root)

    @on_trait_change('active_editor:gosub_event')
    def _handle_selected_gosub(self, new):

        self.debug('selected gosub {}'.format(new))
        if new:
            root = os.path.dirname(self.active_editor.path)
            self._open_pyscript(new, root)
            # self.active_editor.trait_set(selected_gosub='', trait_change_notify=False)

    @on_trait_change('active_editor:selected_command')
    def _handle_selected_command(self, new):
        self.debug('selected command {}'.format(new))
        if new:
            self.commands_pane.set_command(new)

    def _runner_factory(self):
        runner = self.application.get_service('pychron.extraction_line.ipyscript_runner.IPyScriptRunner')
        # get the extraction line manager's mode
        # man = self._get_el_manager()
        #
        # if man is None:
        #     self.warning_dialog('No Extraction line manager available')
        #     mode = 'normal'
        # else:
        #     mode = man.mode
        #
        # if mode == 'client':
        #     #            em = self.extraction_line_manager
        #     from pychron.envisage.initialization.initialization_parser import InitializationParser
        #
        #     ip = InitializationParser()
        #     # elm = ip.get_plugin('Experiment', category='general')
        #     elm = ip.get_plugin('ExtractionLine', category='hardware')
        #     runner = elm.find('runner')
        #     host, port, kind = None, None, None
        #
        #     if runner is not None:
        #         comms = runner.find('communications')
        #         host = comms.find('host')
        #         port = comms.find('port')
        #         kind = comms.find('kind')
        #
        #     if host is not None:
        #         host = host.text  # if host else 'localhost'
        #     if port is not None:
        #         port = int(port.text)  # if port else 1061
        #     if kind is not None:
        #         kind = kind.text  # if kind else 'udp'
        #
        #     from pychron.extraction_line.pyscript_runner import RemotePyScriptRunner
        #
        #     runner = RemotePyScriptRunner(host, port, kind)
        # else:
        #     from pychron.extraction_line.pyscript_runner import PyScriptRunner
        #
        #     runner = PyScriptRunner()

        return runner

    #defaults
    def _repo_manager_default(self):
        from pychron.git_archive.repo_manager import GitRepoManager

        return GitRepoManager(application=self.application)

    def _default_layout_default(self):
        left = Splitter(Tabbed(PaneItem('pychron.pyscript.commands', height=300, width=125),
                               PaneItem('pychron.pyscript.script_browser')),
                        PaneItem('pychron.pyscript.commands_editor', height=100, width=125),
                        orientation='vertical')
        # bottom = PaneItem('pychron.pyscript.description')
        if self.use_git_repo:
            right = Tabbed(PaneItem('pychron.pyscript.repo'),
                           PaneItem('pychron.pyscript.context_editor'))
        else:
            right = PaneItem('pychron.pyscript.context_editor')

        return TaskLayout(id='pychron.pyscript',
                          left=left,
                          right=right)
        # ============= EOF =============================================
