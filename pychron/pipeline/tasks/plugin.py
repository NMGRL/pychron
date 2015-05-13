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
from envisage.ui.tasks.task_factory import TaskFactory
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.pipeline.tasks.preferences import PipelinePreferencesPane
from pychron.pipeline.tasks.task import PipelineTask
from pychron.envisage.browser.browser_model import BrowserModel


class PipelinePlugin(BaseTaskPlugin):
    def _pipeline_factory(self):
        model = self.application.get_service(BrowserModel)
        t = PipelineTask(browser_model=model)
        return t

    def _browser_model_factory(self):
        return BrowserModel(application=self.application)

    # defaults
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=BrowserModel,
                                        factory=self._browser_model_factory)
        return [so]

    def _preferences_panes_default(self):
        return [PipelinePreferencesPane]

    def _task_extensions_default(self):
        # return [TaskExtension(actions=[SchemaAddition(id='Flag Manager',
        # factory=OpenFlagManagerAction,
        # path='MenuBar/tools.menu'), ])]
        return []

    def _tasks_default(self):
        return [TaskFactory(id='pychron.pipeline.task.factory',
                            name='Pipeline',
                            accelerator='Ctrl+p',
                            factory=self._pipeline_factory)]

# ============= EOF =============================================



