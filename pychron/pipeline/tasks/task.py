# ===============================================================================
# Copyright 2015 Jake Ross
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
import os

from pyface.tasks.action.schema import SToolBar, SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter
from traits.api import Instance, Bool, on_trait_change

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.pipeline.engine import PipelineEngine
from pychron.pipeline.state import EngineState
from pychron.pipeline.tasks.actions import RunAction, SavePipelineTemplateAction, ResumeAction, ResetAction, \
    ConfigureRecallAction
from pychron.pipeline.tasks.panes import PipelinePane, AnalysesPane
from pychron.envisage.browser.browser_task import BaseBrowserTask

DEBUG = True


class DataMenu(SMenu):
    id = 'data.menu'
    name = 'Data'


class PipelineTask(BaseBrowserTask):
    name = 'Pipeline Processing'
    engine = Instance(PipelineEngine, ())
    tool_bars = [SToolBar(RunAction(),
                          ResumeAction(),
                          ResetAction(),
                          ConfigureRecallAction(),
                          SavePipelineTemplateAction()),
                 # SToolBar(SwitchToBrowserAction())
                 ]
    state = Instance(EngineState)
    resume_enabled = Bool(False)
    run_enabled = Bool(True)
    # reset_enabled = Bool(False)
    run_to = None
    # def switch_to_browser(self):
    #     self._activate_task('pychron.browser.task')

    modified = False
    dbmodified = False
    projects = None

    # def _opened_hook(self):
        # super(PipelineTask, self)._opened_hook()
        # self._debug()
        # if DEBUG:
        #     do_after(500, self._debug)

    def activated(self):
        super(PipelineTask, self).activated()

        self.engine.dvc = self.dvc
        self.engine.browser_model = self.browser_model
        self.engine.on_trait_change(self._handle_run_needed, 'run_needed')
        self.engine.on_trait_change(self._handle_recall, 'recall_analyses_needed')

        self.engine.task = self
        self.engine.add_data()

    def _debug(self):
        self.engine.add_data()
        self.engine.select_default()
        self.engine.set_template('icfactor')
        # self.engine.add_is
        # self.engine.add_grouping(run=False)
        # self.engine.add_test_filter()
        # self.engine.add_ideogram(run=False)
        # self.engine.add_series(run=False)

        # self.engine.add_test_filter()
        # self.engine.add_ideogram()
        # self.engine.add_pdf_figure_node()
        # self.engine.add_spectrum()

        # self.run()

    def prepare_destroy(self):
        pass

    def create_dock_panes(self):
        panes = [PipelinePane(model=self.engine),
                 AnalysesPane(model=self.engine)]
        return panes

    # toolbar actions
    def reset(self):
        self.state = None
        self.engine.reset()

    def save_pipeline_template(self):
        # path = self.save_file_dialog()
        # path = '/Users/ross/Sandbox/template.yaml'
        path = os.path.join(paths.pipeline_template_dir, 'test.yaml')
        if path:
            self.engine.save_pipeline_template(path)

    def run(self):
        self._run_pipeline()

    def _close_editor(self, editor):
        for e in self.editor_area.editors:
            if e.name == editor.name:
                self.close_editor(e)
                break

    def _run_pipeline(self):
        self.debug('run pipeline')
        if self.state:
            self.debug('using previous state')
            state = self.state
        else:
            state = EngineState()

        if not self.engine.run(state, self.run_to):
            self.state = state
            self._toggle_run(True)
        else:
            self._toggle_run(False)
            self.state = None

        self.close_all()
        for editor in state.editors:
            self._close_editor(editor)
            self._open_editor(editor)

        self.engine.selected = None
        self.engine.update_needed = True

        if state.dbmodified:
            self.dbmodified = True

    def _toggle_run(self, v):
        self.resume_enabled = v
        self.run_enabled = not v

    def _default_layout_default(self):
        return TaskLayout(left=Splitter(PaneItem('pychron.pipeline.pane',
                                                 width=200),
                                        PaneItem('pychron.pipeline.analyses',
                                                 width=200)))

    def _extra_actions_default(self):
        sas = (('MenuBar', DataMenu, {'before': 'tools.menu', 'after': 'view.menu'}),
               ('MenuBar/data.menu', RunAction, {}))
        return [self._sa_factory(path, factory, **kw) for path, factory, kw in sas]

    def _sa_factory(self, path, factory, **kw):
        return SchemaAddition(path=path, factory=factory, **kw)

    # handlers
    @on_trait_change('engine:unknowns[]')
    def _handle_unknowns(self, name, old, new):
        if self.active_editor:
            if not new:
                self.active_editor.set_items(self.engine.unknowns)
                self.active_editor.refresh_needed = True
        self.engine.update_detectors()

    @on_trait_change('engine:references[]')
    def _handle_references(self, name, old, new):
        if self.active_editor:
            # only update if deletion
            if not new:
                self.active_editor.set_references(self.engine.references)
                self.active_editor.refresh_needed = True
        self.engine.update_detectors()

    def _active_editor_changed(self, new):
        if new:
            self.engine.select_node_by_editor(new)

    def _handle_run_needed(self, new):
        self.debug('run needed for {}'.format(new))
        self.run()

    def _handle_recall(self, new):
        self.recall(new)


    def _prompt_for_save(self):
        ret = True
        ps = self.engine.get_projects()
        if ps:
            changed = self.dvc.project_has_staged(ps)
            if changed:
                m = 'You have changes to analyses. Would you like to share them?'
                ret = self._handle_prompt_for_save(m, 'Share Changes')
                if ret == 'save':
                    self.dvc.push_projects(ps)

        return ret
# ============= EOF =============================================
