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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter
from pyface.timer.do_later import do_after
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.engine import PipelineEngine
from pychron.pipeline.state import EngineState
from pychron.pipeline.tasks.actions import RunAction
from pychron.pipeline.tasks.panes import PipelinePane, AnalysesPane
from pychron.envisage.browser.browser_task import BaseBrowserTask


DEBUG = True


class PipelineTask(BaseBrowserTask):
    engine = Instance(PipelineEngine, ())
    tool_bars = [SToolBar(RunAction())]

    def activated(self):
        super(PipelineTask, self).activated()

        dvc = self.application.get_service('pychron.dvc.dvc.DVC')
        self.engine.dvc = dvc
        self.engine.browser_model = self.browser_model
        self.engine.on_trait_change(self._handle_run_needed, 'run_needed')

        self.engine.task = self
        if DEBUG:
            do_after(1000, self._debug)

    def _handle_run_needed(self):
        self.run()

    def _debug(self):
        self.engine.add_data()
        self.engine.select_default()
        # self.engine.add_test_filter()
        self.engine.add_ideogram()
        # self.engine.add_spectrum()

        self.run()

    def prepare_destroy(self):
        pass

    def create_dock_panes(self):
        panes = [PipelinePane(model=self.engine),
                 AnalysesPane(model=self.engine)]
        return panes

    # toolbar actions
    def run(self):
        self._run_pipeline()

    def _close_editor(self, editor):
        for e in self.editor_area.editors:
            if e.name == editor.name:
                self.close_editor(e)
                break

    def _run_pipeline(self):
        self.debug('run pipeline')
        state = EngineState()

        self.engine.run(state)

        for editor in state.editors:
            self._close_editor(editor)
            self._open_editor(editor)

    def _default_layout_default(self):
        return TaskLayout(left=Splitter(PaneItem('pychron.pipeline.pane',
                                                 width=200),
                                        PaneItem('pychron.pipeline.analyses',
                                                 width=200)))

# ============= EOF =============================================



