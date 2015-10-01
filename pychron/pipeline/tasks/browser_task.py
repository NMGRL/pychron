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
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.envisage.browser.view import PaneBrowserView
from pychron.envisage.view_util import open_view
from pychron.globals import globalv
from pychron.pipeline.tasks.actions import ConfigureRecallAction, ConfigureAnalysesTableAction, LoadReviewStatusAction, \
    EditAnalysisAction
from pychron.processing.analyses.view.edit_analysis_view import AnalysisEditView


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
                          LoadReviewStatusAction()),
                 SToolBar(EditAnalysisAction(),
                          name='Edit')]

    def _opened_hook(self):
        super(BrowserTask, self)._opened_hook()
        if globalv.browser_debug:
            r = self.browser_model.analysis_table.analyses[0]
            self.recall(r)

    # toolbar actions
    def edit_analysis(self):
        self.debug('Edit analysis data')
        if not self.has_active_editor():
            return
        #
        editor = self.active_editor
        if hasattr(editor, 'edit_view') and editor.edit_view:
            editor.edit_view.show()
        else:

            e = AnalysisEditView(editor, dvc=self.dvc)

            # e.load_isotopes()
            # info = e.edit_traits()
            # info = timethis(e.edit_traits)
            info = open_view(e)
            e.control = info.control
            editor.edit_view = e

    def create_dock_panes(self):
        return [BrowserPane(model=self.browser_model)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.browser.pane'))

# ============= EOF =============================================
