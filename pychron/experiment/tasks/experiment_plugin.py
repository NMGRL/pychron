# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.action.group import Group
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.sensitivity_entry import SensitivitySelector
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
# from pychron.experiment.experiment_executor import ExperimentExecutor
from pychron.experiment.experimentor import Experimentor
from pychron.experiment.signal_calculator import SignalCalculator
from pychron.experiment.image_browser import ImageBrowser
from pychron.experiment.tasks.experiment_task import ExperimentEditorTask
from pychron.experiment.tasks.experiment_preferences import ExperimentPreferencesPane, ConsolePreferencesPane, \
    SysLoggerPreferencesPane, \
    UserNotifierPreferencesPane, LabspyPreferencesPane
from pychron.experiment.tasks.experiment_actions import NewExperimentQueueAction, \
    OpenExperimentQueueAction, SignalCalculatorAction, \
    DeselectAction, SendTestNotificationAction, \
    NewPatternAction, OpenPatternAction, ResetQueuesAction, OpenLastExperimentQueueAction, UndoAction, \
    QueueConditionalsAction


class ExperimentPlugin(BaseTaskPlugin):
    id = 'pychron.experiment'
    experimentor = Instance(Experimentor)

    def _actions_default(self):
        return [('pychron.open_experiment', 'Ctrl+O', 'Open Experiment'),
                ('pychron.new_experiment', 'Ctrl+N', 'New Experiment'),
                ('pychron.deselect', 'Ctrl+Shift+D', 'Deselect'),
                ('pychron.open_last_experiment', 'Alt+Ctrl+O', 'Open Last Experiment')]

    def _my_task_extensions_default(self):
        factory = lambda: Group(DeselectAction(),
                                ResetQueuesAction(),
                                UndoAction())

        return [TaskExtension(task_id='pychron.experiment.task',
                              actions=[SchemaAddition(
                                  factory=factory,
                                  path='MenuBar/Edit')]),
                TaskExtension(actions=[
                    SchemaAddition(id='open_queue_conditionals',
                                   factory=QueueConditionalsAction,
                                   path='MenuBar/Edit'),
                    SchemaAddition(id='open_experiment',
                                   factory=OpenExperimentQueueAction,
                                   path='MenuBar/file.menu/Open'),
                    SchemaAddition(id='open_last_experiment',
                                   factory=OpenLastExperimentQueueAction,
                                   path='MenuBar/file.menu/Open'),
                    SchemaAddition(id='test_notify',
                                   factory=SendTestNotificationAction,
                                   path='MenuBar/file.menu'),
                    SchemaAddition(id='new_experiment',
                                   factory=NewExperimentQueueAction,
                                   path='MenuBar/file.menu/New'),
                    SchemaAddition(id='signal_calculator',
                                   factory=SignalCalculatorAction,
                                   path='MenuBar/Tools'),
                    SchemaAddition(id='new_pattern',
                                   factory=NewPatternAction,
                                   path='MenuBar/file.menu/New'),
                    SchemaAddition(id='open_pattern',
                                   factory=OpenPatternAction,
                                   path='MenuBar/file.menu/Open')])]

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
        # so_ex = self.service_offer_factory(protocol=Experimentor,
        #                                    factory=self._experimentor_factory)
        return [so_signal_calculator,
                so_image_browser,
                so_sens_selector,
                # so_ex
                ]

    # def _experimentor_factory(self):
    #     return self.experimentor

    def _experimentor_default(self):
        # from pychron.experiment.experimentor import Experimentor
        # from pychron.initialization_parser import InitializationParser
        from pychron.envisage.initialization.initialization_parser import InitializationParser

        ip = InitializationParser()
        plugin = ip.get_plugin('Experiment', category='general')
        mode = ip.get_parameter(plugin, 'mode')

        # app = None
        # if self.window:
        #     app = self.window.application

        exp = Experimentor(application=self.application,
                           mode=mode)

        return exp

    def _signal_calculator_factory(self, *args, **kw):
        return SignalCalculator()

    def _sens_selector_factory(self, *args, **kw):
        return SensitivitySelector()

    def _image_browser_factory(self, *args, **kw):
        return ImageBrowser(application=self.application)

    def _tasks_default(self):
        return [TaskFactory(id='pychron.experiment.task',
                            factory=self._task_factory,
                            name='Experiment',
                            image='applications-science',
                            task_group='experiment')]

    def _task_factory(self):
        return ExperimentEditorTask(manager=self.experimentor)

    def _preferences_panes_default(self):
        return [ExperimentPreferencesPane,
                LabspyPreferencesPane,
                ConsolePreferencesPane,
                SysLoggerPreferencesPane,
                UserNotifierPreferencesPane]

        # ============= EOF =============================================
