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
from pyface.tasks.action.schema import SGroup
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.entry.entry_views.sensitivity_entry import SensitivitySelector
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.signal_calculator import SignalCalculator
from pychron.experiment.tasks.experiment_actions import NewExperimentQueueAction, \
    OpenExperimentQueueAction, SignalCalculatorAction, \
    DeselectAction, SendTestNotificationAction, \
    NewPatternAction, OpenPatternAction, ResetQueuesAction, OpenLastExperimentQueueAction, UndoAction, \
    QueueConditionalsAction, ConfigureEditorTableAction, SystemConditionalsAction, ResetSystemHealthAction, \
    OpenExperimentHistoryAction, LastAnalysisRecoveryAction, OpenCurrentExperimentQueueAction, \
    SaveAsCurrentExperimentAction, SyncQueueAction, AcquireSpectrometerAction, ReleaseSpectrometerAction
from pychron.experiment.tasks.experiment_preferences import ExperimentPreferencesPane, ConsolePreferencesPane, \
    UserNotifierPreferencesPane
from pychron.experiment.tasks.experiment_task import ExperimentEditorTask


class ExperimentPlugin(BaseTaskPlugin):
    id = 'pychron.experiment.plugin'

    # def start(self):
    #     super(ExperimentPlugin, self).start()
    #     # manager = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
    #     dvc = self.application.get_service('pychron.dvc.dvc.DVC')
    #     self.experimentor.dvc = dvc
    #     # self.experimentor.iso_db_manager = manager
    #     self.experimentor.executor.set_managers()
    #     self.experimentor.executor.bind_preferences()

    def _signal_calculator_factory(self, *args, **kw):
        return SignalCalculator()

    def _sens_selector_factory(self, *args, **kw):
        return SensitivitySelector()

    # def _image_browser_factory(self, *args, **kw):
    #     return ImageBrowser(application=self.application)

    def _tasks_default(self):
        return [TaskFactory(id='pychron.experiment.task',
                            factory=self._task_factory,
                            name='Experiment',
                            image='applications-science',
                            task_group='experiment')]

    def _task_factory(self):
        # return ExperimentEditorTask(manager=self.experimentor)
        return ExperimentEditorTask(application=self.application)

    def _preferences_default(self):
        return self._preferences_factory('experiment')

    def _preferences_panes_default(self):
        return [ExperimentPreferencesPane,
                # LabspyPreferencesPane,
                # DVCPreferencesPane,
                ConsolePreferencesPane,
                UserNotifierPreferencesPane]

    def _file_defaults_default(self):
        return [('experiment_defaults', 'EXPERIMENT_DEFAULTS', False)]

    def _actions_default(self):
        return [('pychron.open_experiment', 'Ctrl+O', 'Open Experiment'),
                ('pychron.new_experiment', 'Ctrl+N', 'New Experiment'),
                ('pychron.deselect', 'Ctrl+Shift+D', 'Deselect'),
                ('pychron.open_last_experiment', 'Alt+Ctrl+O', 'Open Last Experiment')]

    def _help_tips_default(self):
        return ['You can set the Analysis State colors in Preferences>Experiment',
                'You can set the color for Sniff, Signal, and Baseline datapoints in Preferences>Experiment',
                'The current version of Pychron contains over 140K lines of code',
                'If the last analysis fails to save you can recover it using Tools/Recover Last Analysis']

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

        sr_actions = [SchemaAddition(id='experiment.acquire_spectrometer',
                                     factory=AcquireSpectrometerAction,
                                     path='MenuBar/Tools'),
                      SchemaAddition(id='experiment.release_spectrometer',
                                     factory=ReleaseSpectrometerAction,
                                     path='MenuBar/Tools')]
        extensions.append(TaskExtension(actions=sr_actions, task_id=''))
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
                  SchemaAddition(id='pychron.experiment.open_current_experiment',
                                 factory=OpenCurrentExperimentQueueAction,
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
                                 path='MenuBar/tools.menu'),
                  SchemaAddition(id='pychron.experiment.last_analysis_recovery', factory=LastAnalysisRecoveryAction,
                                 path='MenuBar/tools.menu'),
                  SchemaAddition(id='pychron.experiment.new_pattern', factory=NewPatternAction,
                                 path='MenuBar/file.menu/New'),
                  SchemaAddition(id='pychron.experiment.open_pattern', factory=OpenPatternAction,
                                 path='MenuBar/file.menu/Open')]),
                ('{}.edit'.format(self.id), 'pychron.experiment.task', 'ExperimentEdit',
                 [SchemaAddition(id='pychron.experiment.edit.deselect', factory=DeselectAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.reset', factory=ResetQueuesAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.sync', factory=SyncQueueAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.undo', factory=UndoAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.edit.configure', factory=ConfigureEditorTableAction,
                                 path='MenuBar/Edit/experiment.group'),
                  SchemaAddition(id='pychron.experiment.save_as_current_experiment',
                                 factory=SaveAsCurrentExperimentAction,
                                 path='MenuBar/file.menu/Save')
                  ])]

    def _service_offers_default(self):
        so_signal_calculator = self.service_offer_factory(
            protocol=SignalCalculator,
            factory=self._signal_calculator_factory)

        # so_image_browser = self.service_offer_factory(
        #     protocol=ImageBrowser,
        #     factory=self._image_browser_factory)

        so_sens_selector = self.service_offer_factory(
            protocol=SensitivitySelector,
            factory=self._sens_selector_factory)

        return [so_signal_calculator,
                # so_image_browser,
                so_sens_selector]

        #     def _experimentor_default(self):
        #         return self._experimentor_factory()
        #
        #     def _experimentor_factory(self):
        #         # from pychron.experiment.experimentor import Experimentor
        #         # from pychron.initialization_parser import InitializationParser
        #         from pychron.envisage.initialization.initialization_parser import InitializationParser
        #
        #         ip = InitializationParser()
        #         plugin = ip.get_plugin('Experiment', category='general')
        #         mode = ip.get_parameter(plugin, 'mode')
        # # from pychron.database.isotope_database_manager import IsotopeDatabaseManager
        #
        #         # manager = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        #
        #         exp = Experimentor(application=self.application,
        #                            mode=mode)
        #
        #         return exp

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
