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
import os

from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.entry_views.sensitivity_entry import SensitivitySelector
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
# from pychron.experiment.experiment_executor import ExperimentExecutor
from pychron.experiment.experimentor import Experimentor
from pychron.experiment.signal_calculator import SignalCalculator
from pychron.experiment.image_browser import ImageBrowser
from pychron.experiment.tasks.experiment_task import ExperimentEditorTask
from pychron.experiment.tasks.experiment_preferences import ExperimentPreferencesPane, ConsolePreferencesPane, \
    UserNotifierPreferencesPane, LabspyPreferencesPane
from pychron.experiment.tasks.experiment_actions import NewExperimentQueueAction, \
    OpenExperimentQueueAction, SignalCalculatorAction, \
    DeselectAction, SendTestNotificationAction, \
    NewPatternAction, OpenPatternAction, ResetQueuesAction, OpenLastExperimentQueueAction, UndoAction, \
    QueueConditionalsAction, ConfigureEditorTableAction, SystemConditionalsAction, ResetSystemHealthAction, \
    OpenExperimentHistoryAction
from pychron.paths import paths


class ExperimentPlugin(BaseTaskPlugin):
    id = 'pychron.experiment.plugin'
    experimentor = Instance(Experimentor)

    def start(self):
        super(ExperimentPlugin, self).start()
        manager = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        self.experimentor.iso_db_manager = manager
        self.experimentor.executor.set_managers()
        self.experimentor.executor.bind_preferences()

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
        e = ExperimentEditorTask(manager=self.experimentor)
        return e

    def _preferences_default(self):
        return ['file://{}'.format(os.path.join(paths.preferences_dir, 'experiment.ini'))]

    def _preferences_panes_default(self):
        return [ExperimentPreferencesPane,
                LabspyPreferencesPane,
                ConsolePreferencesPane,
                UserNotifierPreferencesPane]

    def _file_defaults_default(self):
        return [('experiment_defaults', 'EXPERIMENT_DEFAULTS', False)]

    def _actions_default(self):
        return [('pychron.open_experiment', 'Ctrl+O', 'Open Experiment'),
                ('pychron.new_experiment', 'Ctrl+N', 'New Experiment'),
                ('pychron.deselect', 'Ctrl+Shift+D', 'Deselect'),
                ('pychron.open_last_experiment', 'Alt+Ctrl+O', 'Open Last Experiment')]

    def _task_extensions_default(self):
        extensions = [TaskExtension(actions=actions, task_id=eid) for eid, actions in self._get_extensions()]
        # print 'a', len(extensions)
        additions = []

        eflag = False
        for eid, actions in self._get_extensions():
            # print 'b', eid, len(actions)
            for ai in actions:
                if not eflag and ai.id.startswith('pychron.experiment.edit'):
                    eflag = True
                    additions.append(SchemaAddition(id='experiment.edit',
                                                    factory=lambda: SGroup(id='experiment.group'),
                                                    path='MenuBar/Edit'), )
        if additions:
            extensions.append(TaskExtension(actions=additions, task_id=''))
        return extensions

    def _available_task_extensions_default(self):
        return [(self.id, '', 'Experiment',
                 [SchemaAddition(id='pychron.experiment.reset_system_health', factory=ResetSystemHealthAction,
                                 path='MenuBar/file.menu'),
                  SchemaAddition(id='pychron.experiment.open_queue_conditionals', factory=QueueConditionalsAction,
                                 path='MenuBar/Edit'),
                  SchemaAddition(id='pychron.experiment.open_system_conditionals', factory=SystemConditionalsAction,
                                 path='MenuBar/Edit'),
                  SchemaAddition(id='pychron.experiment.open_experiment', factory=OpenExperimentQueueAction,
                                 path='MenuBar/file.menu/Open'),
                  SchemaAddition(id='pychron.experiment.open_last_experiment', factory=OpenLastExperimentQueueAction,
                                 path='MenuBar/file.menu/Open'),
                  SchemaAddition(id='pychron.experiment.launch_history', factory=OpenExperimentHistoryAction,
                                 path='MenuBar/file.menu/Open'),
                  SchemaAddition(id='pychron.experiment.test_notify', factory=SendTestNotificationAction,
                                 path='MenuBar/file.menu'),
                  SchemaAddition(id='pychron.experiment.new_experiment', factory=NewExperimentQueueAction,
                                 path='MenuBar/file.menu/New'),
                  SchemaAddition(id='pychron.experiment.signal_calculator', factory=SignalCalculatorAction,
                                 path='MenuBar/Tools'),
                  SchemaAddition(id='pychron.experiment.new_pattern', factory=NewPatternAction,
                                 path='MenuBar/file.menu/New'),
                  SchemaAddition(id='pychron.experiment.open_pattern', factory=OpenPatternAction,
                                 path='MenuBar/file.menu/Open')]),
                ('{}.edit'.format(self.id), 'pychron.experiment.task', 'ExperimentEdit',
                 [SchemaAddition(id='pychron.experiment.edit.deselect', factory=DeselectAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.reset', factory=ResetQueuesAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.undo', factory=UndoAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.configure', factory=ConfigureEditorTableAction,
                                 path='MenuBar/Edit/experiment.group')])]

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

    def _experimentor_default(self):
        return self._experimentor_factory()

    def _experimentor_factory(self):
        # from pychron.experiment.experimentor import Experimentor
        # from pychron.initialization_parser import InitializationParser
        from pychron.envisage.initialization.initialization_parser import InitializationParser

        ip = InitializationParser()
        plugin = ip.get_plugin('Experiment', category='general')
        mode = ip.get_parameter(plugin, 'mode')
# from pychron.database.isotope_database_manager import IsotopeDatabaseManager

        # manager = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        # print 'get exp man', manager
        exp = Experimentor(application=self.application,
                           # iso_db_manager=manager,
                           # manager=manager,
                           mode=mode)

        return exp

# ============= EOF =============================================
# factory = lambda: Group(DeselectAction(),
# ResetQueuesAction(),
# UndoAction(),
#                         ConfigureEditorTableAction())
#
# return [TaskExtension(task_id='pychron.experiment.task',
#                       actions=[SchemaAddition(factory=factory,
#                                               path='MenuBar/Edit')]),
#         TaskExtension(actions=[
#             SchemaAddition(id='reset_system_health',
#                            factory=ResetSystemHealthAction,
#                            path='MenuBar/file.menu'),
#             SchemaAddition(id='open_queue_conditionals',
#                            factory=QueueConditionalsAction,
#                            path='MenuBar/Edit'),
#             SchemaAddition(id='open_queue_conditionals',
#                            factory=SystemConditionalsAction,
#                            path='MenuBar/Edit'),
#             SchemaAddition(id='open_experiment',
#                            factory=OpenExperimentQueueAction,
#                            path='MenuBar/file.menu/Open'),
#             SchemaAddition(id='open_last_experiment',
#                            factory=OpenLastExperimentQueueAction,
#                            path='MenuBar/file.menu/Open'),
#             SchemaAddition(id='test_notify',
#                            factory=SendTestNotificationAction,
#                            path='MenuBar/file.menu'),
#             SchemaAddition(id='new_experiment',
#                            factory=NewExperimentQueueAction,
#                            path='MenuBar/file.menu/New'),
#             SchemaAddition(id='signal_calculator',
#                            factory=SignalCalculatorAction,
#                            path='MenuBar/Tools'),
#             SchemaAddition(id='new_pattern',
#                            factory=NewPatternAction,
#                            path='MenuBar/file.menu/New'),
#             SchemaAddition(id='open_pattern',
#                            factory=OpenPatternAction,
#                            path='MenuBar/file.menu/Open')])]