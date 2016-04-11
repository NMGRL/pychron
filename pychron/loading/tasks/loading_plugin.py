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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition

# from pyface.action.group import Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.loading.tasks.load_task import LoadingTask
from pychron.loading.tasks.actions import SaveLoadingPDFAction, SaveTrayPDFAction, GenerateResultsAction
from pychron.loading.tasks.loading_preferences import LoadingPreferencesPane
from pychron.loading.tasks.panes import LoadDockPane, LoadTablePane
from pychron.loading.loading_manager import LoadingManager


class LoadingPlugin(BaseTaskPlugin):
    id = 'pychron.loading'

    def _task_extensions_default(self):
        actions = [SchemaAddition(id='save_loading_figure',
                                  factory=SaveLoadingPDFAction,
                                  path='MenuBar/file.menu'),
                   SchemaAddition(id='save_tray',
                                  factory=SaveTrayPDFAction,
                                  path='MenuBar/file.menu'),
                   SchemaAddition(id='generate_results',
                                  factory=GenerateResultsAction,
                                  path='MenuBar/file.menu')]
        return [TaskExtension(task_id='pychron.loading',
                              actions=actions)]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.loading',
                            factory=self._load_task_factory,
                            name='Loading',
                            accelerator='Ctrl+Y',
                            task_group='experiment')]

    def _service_offers_default(self):
        load = self.service_offer_factory(protocol=LoadDockPane,
                                          factory=LoadDockPane)
        table = self.service_offer_factory(protocol=LoadTablePane,
                                           factory=LoadTablePane)
        man = self.service_offer_factory(protocol=LoadingManager,
                                         factory=LoadingManager,
                                         properties={
                                             'application': self.application})

        return [load, table, man]

    def _load_task_factory(self):
        return LoadingTask(manager=LoadingManager(application=self.application))

    def _preferences_panes_default(self):
        return [LoadingPreferencesPane]

# ============= EOF =============================================
