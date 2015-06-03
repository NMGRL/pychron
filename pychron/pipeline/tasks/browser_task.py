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
from pyface.tasks.task_layout import TaskLayout, PaneItem
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.envisage.browser.view import BrowserView


class BrowserPane(TraitsDockPane, BrowserView):
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
    # tool_bars = [SToolBar(ToPipelineAction())]

    # def switch_to_pipeline(self):
    #     self._activate_task('pychron.pipeline.task')

    def create_dock_panes(self):
        return [BrowserPane(model=self.browser_model)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.browser.pane'))

# ============= EOF =============================================
