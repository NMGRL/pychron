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
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.action.group import Group
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.entry.sensitivity_entry import SensitivitySelector
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.signal_calculator import SignalCalculator
from pychron.experiment.image_browser import ImageBrowser
from pychron.experiment.tasks.experiment_task import ExperimentEditorTask
from pychron.experiment.tasks.experiment_preferences import ExperimentPreferencesPane, ConsolePreferencesPane, \
    SysLoggerPreferencesPane, \
    UserNotifierPreferencesPane
from pychron.experiment.tasks.experiment_actions import NewExperimentQueueAction, \
    OpenExperimentQueueAction, SignalCalculatorAction, \
    DeselectAction, SendTestNotificationAction, \
    NewPatternAction, OpenPatternAction, ResetQueuesAction, OpenLastExperimentQueueAction, UndoAction, \
    QueueConditionsAction


class ExperimentPlugin(BaseTaskPlugin):
    id = 'pychron.experiment'

    def _my_task_extensions_default(self):
        factory = lambda: Group(DeselectAction(),
                                ResetQueuesAction(),
                                UndoAction())

        return [TaskExtension(task_id='pychron.experiment',
                              actions=[SchemaAddition(
                                  factory=factory,
                                  path='MenuBar/Edit')]),
                TaskExtension(actions=[
                    SchemaAddition(id='open_queue_conditions',
                                   factory=QueueConditionsAction,
                                   path='MenuBar/Edit'),
                    SchemaAddition(id='open_experiment',
                                   factory=OpenExperimentQueueAction,
                                   path='MenuBar/File/Open'),
                    SchemaAddition(id='open_last_experiment',
                                   factory=OpenLastExperimentQueueAction,
                                   path='MenuBar/File/Open'),
                    SchemaAddition(id='test_notify',
                                   factory=SendTestNotificationAction,
                                   path='MenuBar/File'),
                    SchemaAddition(id='new_experiment',
                                   factory=NewExperimentQueueAction,
                                   path='MenuBar/File/New'),
                    SchemaAddition(id='signal_calculator',
                                   factory=SignalCalculatorAction,
                                   path='MenuBar/Tools'),
                    SchemaAddition(id='new_pattern',
                                   factory=NewPatternAction,
                                   path='MenuBar/File/New'),
                    SchemaAddition(id='open_pattern',
                                   factory=OpenPatternAction,
                                   path='MenuBar/File/Open')])]

    def _service_offers_default(self):
        so_signal_calculator = self.service_offer_factory(
            protocol=SignalCalculator,
            factory=self._signal_calculator_factory)

        so_image_browser = self.service_offer_factory(
            protocol=ImageBrowser,
            factory=self._image_browser_factory)

        so_sens_selector = self.service_offer_factory(
            protocol=SensitivitySelector,
            factory=self._sens_selector_factory)

        return [so_signal_calculator,
                so_image_browser,
                so_sens_selector]

    def _signal_calculator_factory(self, *args, **kw):
        return SignalCalculator()

    def _sens_selector_factory(self, *args, **kw):
        return SensitivitySelector()

    def _image_browser_factory(self, *args, **kw):
        return ImageBrowser(application=self.application)

    def _tasks_default(self):
        return [TaskFactory(id=self.id,
                            factory=self._task_factory,
                            name='Experiment',
                            image='applications-science',
                            task_group='experiment')]


    def _task_factory(self):
        return ExperimentEditorTask()

    def _preferences_panes_default(self):
        return [ExperimentPreferencesPane,
                ConsolePreferencesPane,
                SysLoggerPreferencesPane,
                UserNotifierPreferencesPane]

        #============= EOF =============================================
