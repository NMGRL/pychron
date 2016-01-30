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
from pyface.tasks.task_layout import TaskLayout, PaneItem
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Instance, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.envisage.browser.view import PaneBrowserView
from pychron.envisage.tasks.actions import ToggleFullWindowAction
from pychron.globals import globalv
from pychron.pipeline.tasks.actions import ConfigureRecallAction, ConfigureAnalysesTableAction, \
    LoadReviewStatusAction, EditAnalysisAction, DiffViewAction


class BrowserPane(TraitsDockPane, PaneBrowserView):
    id = 'pychron.browser.pane'
    name = 'Analysis Selection'

    # def trait_context(self):
    #     return {'object':self.model, 'pane':self}
    #
    # def traits_view(self):
    #     bv = BrowserView(model=self.model)
    #     return bv.traits_view()


# class ToPipelineAction(TaskAction):
#     name = 'To Pipeline'
#     method = 'switch_to_pipeline'
#     image = icon('play')


class BrowserTask(BaseBrowserTask):
    name = 'Analysis Browser'

    model = Instance('pychron.envisage.browser.browser_model.BrowserModel')
    tool_bars = [SToolBar(ConfigureRecallAction(),
                          ConfigureAnalysesTableAction(),
                          name='Configure'),
                 SToolBar(ToggleFullWindowAction(),
                          LoadReviewStatusAction(),
                          DiffViewAction(),
                          name='View'),
                 SToolBar(EditAnalysisAction(),
                          name='Edit')]

    diff_enabled = Bool

    def activated(self):
        if self.application.get_plugin('pychron.mass_spec.plugin'):
            self.diff_enabled = True
        super(BrowserTask, self).activated()

    def _opened_hook(self):
        super(BrowserTask, self)._opened_hook()

        self.browser_model.activated()
        self._activate_sample_browser()

        if globalv.browser_debug:
            if self.browser_model.analysis_table.analyses:
                r = self.browser_model.analysis_table.analyses[0]
                self.recall(r)

    # toolbar actions

    def diff_analysis(self):
        self.debug('Edit analysis data')
        if not self.has_active_editor():
            return

        recaller = self.application.get_service('pychron.mass_spec.mass_spec_recaller.MassSpecRecaller')
        if recaller is None:
            return

        active_editor = self.active_editor
        left = active_editor.analysis

        from pychron.pipeline.editors.diff_editor import DiffEditor
        editor = DiffEditor(recaller=recaller)
        left.load_raw_data()
        if editor.setup(left):
            editor.set_diff(left)
            self._open_editor(editor)

    def create_dock_panes(self):
        return [BrowserPane(model=self.browser_model)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.browser.pane'))

# ============= EOF =============================================
