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
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
# from pyface.action.group import Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
# from pychron.experiment.signal_calculator import SignalCalculator
# from pychron.experiment.image_browser import ImageBrowser
# from pychron.experiment.tasks.experiment_task import ExperimentEditorTask
# from pychron.experiment.tasks.experiment_preferences import ExperimentPreferencesPane
# from pychron.experiment.tasks.experiment_actions import NewExperimentQueueAction, \
#     OpenExperimentQueueAction, SaveExperimentQueueAction, \
#     SaveAsExperimentQueueAction, SignalCalculatorAction, \
#     UpdateDatabaseAction, DeselectAction, SendTestNotificationAction, \
#     NewPatternAction, OpenPatternAction, ResetQueuesAction
# from pychron.experiment.tasks.constants_preferences import ConstantsPreferencesPane
# from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.loading.load_task import LoadingTask
from pychron.loading.actions import SaveLoadingAction
from pychron.loading.loading_preferences import LoadingPreferencesPane
from pychron.loading.panes import LoadDockPane, LoadTablePane
from pychron.loading.loading_manager import LoadingManager


class LoadingPlugin(BaseTaskPlugin):
    id = 'pychron.loading'

    def _my_task_extensions_default(self):
        return [TaskExtension(task_id='pychron.loading',
                              actions=[SchemaAddition(id='save_loading_figure',
                                                      factory=SaveLoadingAction,
                                                      path='MenuBar/file.menu')])]

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
                                         factory=self._loading_manager_factory)
        return [load, table, man]

    def _loading_manager_factory(self):
        return LoadingManager(connect=False)

    def _load_task_factory(self):
        lm = self.application.get_service(LoadingManager)
        lm.db.connect()
        return LoadingTask(manager=lm)

    def _preferences_panes_default(self):
        return [LoadingPreferencesPane]

# ============= EOF =============================================
