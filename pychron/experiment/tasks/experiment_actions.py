#===============================================================================
# Copyright 2011 Jake Ross
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
import os

from pyface.message_dialog import warning
from pyface.action.api import Action
from pyface.tasks.task_window_layout import TaskWindowLayout
from pyface.tasks.action.task_action import TaskAction


#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.paths import paths


class ExperimentAction(Action):
    task_id = 'pychron.experiment'

    def _get_experimentor(self, event):
        return self._get_service(event, 'pychron.experiment.experimentor.Experimentor')

    def _get_service(self, event, name):
        app = event.task.window.application
        return app.get_service(name)

    def _open_editor(self, event):
        application = event.task.window.application
        application.open_task(self.task_id)

        #         for wi in application.windows:


#             if wi.active_task.id == self.task_id:
#                 wi.activate()
#                 break
#         else:
#             win = application.create_window(TaskWindowLayout(self.task_id))
#             win.open()

class BasePatternAction(TaskAction):
    _enabled = None

    def _task_changed(self):
        if self.task:
            if hasattr(self.task, 'open_pattern'):
                enabled = True
                if self.enabled_name:
                    if self.object:
                        enabled = bool(self._get_attr(self.object,
                                                      self.enabled_name, False))
                if enabled:
                    self._enabled = True
            else:
                self._enabled = False

    def _enabled_update(self):
        """
             reimplement ListeningAction's _enabled_update
        """
        if self.enabled_name:
            if self.object:
                self.enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
            else:
                self.enabled = False
        elif self._enabled is not None:
            self.enabled = self._enabled
        else:
            self.enabled = bool(self.object)


class OpenPatternAction(BasePatternAction):
    name = 'Open Pattern...'
    method = 'open_pattern'


class NewPatternAction(BasePatternAction):
    name = 'New Pattern...'
    method = 'new_pattern'


class SendTestNotificationAction(TaskAction):
    name = 'Send Test Notification'
    method = 'send_test_notification'
    accelerator = 'Ctrl+Shift+N'


class DeselectAction(TaskAction):
    name = 'Deselect'
    method = 'deselect'
    accelerator = 'Ctrl+Shift+D'
    tooltip = 'Deselect the selected run(s)'


class UndoAction(TaskAction):
    name = 'Undo'
    method = 'undo'
    accelerator = 'Ctrl+Z'


class QueueAction(ExperimentAction):
    def _open_experiment(self, event, path=None):

        app = event.task.window.application
        task = event.task
        if task.id == 'pychron.experiment':
            task.open(path)
        else:
            task = app.get_task('pychron.experiment', False)
            if task.open(path):
                task.window.open()


class NewExperimentQueueAction(QueueAction):
    description = 'Create a new experiment queue'
    name = 'New Experiment'
    accelerator = 'Ctrl+N'

    def perform(self, event):
        if event.task.id == 'pychron.experiment':
            event.task.new()
        else:
            application = event.task.window.application
            win = application.create_window(TaskWindowLayout('pychron.experiment'))
            task = win.active_task
            task.new()
            win.open()


class OpenLastExperimentQueueAction(QueueAction):
    description = 'Open last executed experiment'
    name = 'Open Last Experiment...'
    accelerator = 'Alt+Ctrl+O'

    def __init__(self, *args, **kw):
        super(OpenLastExperimentQueueAction, self).__init__(*args, **kw)
        self.enabled = os.path.isfile(paths.last_experiment)

    def perform(self, event):
        if os.path.isfile(paths.last_experiment):
            with open(paths.last_experiment, 'r') as fp:
                path = fp.readline()
                if os.path.isfile(path):
                    self._open_experiment(event, path)
        else:
            warning(None, 'No last experiment available')


class OpenExperimentQueueAction(QueueAction):
    description = 'Open experiment'
    name = 'Open Experiment...'
    accelerator = 'Ctrl+O'
    image = icon('project-open')

    def perform(self, event):
        path = '/Users/ross/Pychrondata_dev/experiments/Current Experiment.txt'
        self._open_experiment(event, path)


class SaveExperimentQueueAction(ExperimentAction):
    name = 'Save Experiment'
    enabled = False
    accelerator = 'Ctrl+s'
    # image = icon('project-save')


    def perform(self, event):
        manager = self._get_experimentor(event)
        manager.save_experiment_queues()

    def _update_state(self, v):
        self.enabled = v


class SaveAsExperimentQueueAction(ExperimentAction):
    name = 'Save As Experiment...'
    enabled = False
    accelerator = 'Ctrl+Shift+s'

    def perform(self, event):
        manager = self._get_experimentor(event)
        manager.save_as_experiment_queues()


#===============================================================================
# Utilities
#===============================================================================
class SignalCalculatorAction(ExperimentAction):
    name = 'Signal Calculator'

    def perform(self, event):
        obj = self._get_service(event, 'pychron.experiment.signal_calculator.SignalCalculator')
        app = event.task.window.application
        app.open_view(obj)


class ResetQueuesAction(TaskAction):
    method = 'reset_queues'
    name = 'Reset Queues'


#============= EOF ====================================
