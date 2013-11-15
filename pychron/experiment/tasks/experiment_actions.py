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
from traits.api import Any
from pyface.action.api import Action
from pyface.tasks.task_window_layout import TaskWindowLayout
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================

#============= local library imports  ==========================
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
        '''
             reimplement ListeningAction's _enabled_update
        '''
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


class QueueAction(ExperimentAction):
    pass


class NewExperimentQueueAction(QueueAction):
    '''
    '''
    description = 'Create a new experiment queue'
    name = 'New Experiment'
    accelerator = 'Ctrl+N'

    def perform(self, event):
        '''
        '''

        if event.task.id == 'pychron.experiment':
            event.task.new()
        else:
            application = event.task.window.application
            win = application.create_window(TaskWindowLayout('pychron.experiment'))
            task = win.active_task
            task.new()
            win.open()

#            manager = self._get_experimentor(event)
#            if manager.verify_database_connection(inform=True):
#    #        if manager.verify_credentials():
#                if manager.load():
#                    manager.new_experiment_queue()
#                    self._open_editor(event)

class OpenExperimentQueueAction(QueueAction):
    '''
    '''
    description = 'Open experiment set'
    name = 'Open Experiment...'
    accelerator = 'Ctrl+O'

    def perform(self, event):
        '''
        '''
        app = event.task.window.application
        task = event.task
        if task.id == 'pychron.experiment':
            task.open()
        else:
            task = app.get_task('pychron.experiment', False)
            if task.open():
                task.window.open()

#         else:
#             application = event.task.window.application
#             win = application.create_window(TaskWindowLayout('pychron.experiment'))
#             task = win.active_task
#             if task.open():
#                 win.open()


class SaveExperimentQueueAction(ExperimentAction):
    name = 'Save Experiment'
    #     manager = Any
    enabled = False
    accelerator = 'Ctrl+s'
    #     def __init__(self, manager, *args, **kw):
    #         super(SaveExperimentQueueAction, self).__init__(*args, **kw)
    #
    #         manager.on_trait_change(self._update_state, 'save_enabled')
    #         if manager.save_enabled:
    #             self.enabled = True
    #
    #         self.manager = manager

    def perform(self, event):
        manager = self._get_experimentor(event)
        manager.save_experiment_queues()

    def _update_state(self, v):
        self.enabled = v


class SaveAsExperimentQueueAction(ExperimentAction):
    name = 'Save As Experiment...'
    enabled = False
    accelerator = 'Ctrl+Shift+s'
    #     def __init__(self, manager, *args, **kw):
    #         super(SaveAsExperimentQueueAction, self).__init__(*args, **kw)
    #         application = manager.application
    #         application.on_trait_change(self._update_state, 'active_window')

    #     def _update_state(self, win):
    #         if win.active_task:
    #             self.enabled = win.active_task.id == self.task_id

    def perform(self, event):
        manager = self._get_experimentor(event)
        manager.save_as_experiment_queues()

# class MergeQueuesAction(ExperimentAction):
#     name = 'Merge'
#     def perform(self, event):
#         if event.task.id == self.task_id:
#             event.task.merge()

#===============================================================================
# database actions
#===============================================================================
# class LabnumberEntryAction(ExperimentAction):
#    name = 'Labnumber Entry'
#    accelerator = 'Ctrl+Shift+l'
#
#    task_id = 'pychron.labnumber_entry'
#
#    def perform(self, event):
#        app = event.task.window.application
#
#        manager = app.get_service('pychron.experiment.entry.labnumber_entry.LabnumberEntry')
# #        manager = self._get_labnumber_entry(event)
#        if manager.verify_database_connection(inform=True):
# #            lne = manager._labnumber_entry_factory()
#            self._open_editor(event)
# #            open_manager(event.window.application, lne)

#===============================================================================
# Utilities
#===============================================================================
class SignalCalculatorAction(ExperimentAction):
    name = 'Signal Calculator'

    def perform(self, event):
        obj = self._get_service(event, 'pychron.experiment.signal_calculator.SignalCalculator')
        app = event.task.window.application
        app.open_view(obj)

#class UpdateDatabaseAction(ExperimentAction):
#    name = 'Update Database'
#    def perform(self, event):
#        app = event.task.window.application
#        man = app.get_service('pychron.experiment.isotope_database_manager.IsotopeDatabaseManager')
#
#        url = man.db.url
#
#        repo = 'isotopedb'
#        from pychron.database.migrate.manage_database import manage_database
#        progress = man.open_progress()
#        manage_database(url, repo,
#                        logger=man.logger,
#                        progress=progress
#                        )
#
#        man.populate_default_tables()

class ResetQueuesAction(TaskAction):
    method = 'reset_queues'
    name = 'Reset Queues'

#===============================================================================
# deprecated
#===============================================================================
# def mkaction(name, path):
#    def action(cls, event):
#        man = cls._get_executor(event)
#        if man.load_experiment_queue(path=path):
#            open_manager(event.window.application, man)
#
#    nname = '{}Action'.format(name)
#    klass = type(nname, (ExperimentAction,), dict(perform=action,
#                                                    name=name
#                                                    ))
#    globals()[nname] = klass
#===============================================================================
# scripts
#===============================================================================
# class OpenScriptAction(ExperimentAction):
#    def perform(self, event):
#        script_manager = self._get_service(event, 'pychron.pyscripts.manager.PyScriptManager')
#        editor = script_manager.open_script()
#        if editor:
#            open_manager(event.window.application, editor)
#
# class NewScriptAction(ExperimentAction):
#    def perform(self, event):
#        script_editor = self._get_service(event, 'pychron.pyscripts.manager.PyScriptManager')
# #        if script_editor.open_script():
#        open_manager(event.window.application, script_editor)

# class ExecuteProcedureAction(ExperimentAction):
#    def perform(self, event):
#        man = self._get_executor(event)
#        man.execute_procedure()

# class ExecuteExperimentQueueAction(ExperimentAction):
#    name = 'Execute'
#    accelerator = 'Ctrl+W'
#    def perform(self, event):
#        from pychron.globals import globalv
#        man = self._get_executor(event)
# #        man.experiment_set_path = p
# #        if man.verify_credentials(inform=False):
#        if man.verify_database_connection(inform=True):
#            if man.load_experiment_queue(path=globalv.test_experiment_set):
#                open_manager(event.window.application, man)



# class OpenRecentTableAction(ExperimentAction):
#    description = 'Open the Recent Analysis Table'
#    name = 'Lab Table'
#    accelerator = 'Ctrl+R'
#
#    def perform(self, event):
#        manager = self._get_manager(event)
#        manager.open_recent()

##===============================================================================
# # database actions
##===============================================================================
# class LabnumberEntryAction(ExperimentAction):
#    accelerator = 'Ctrl+Shift+l'
#    def perform(self, event):
#        manager = self._get_manager(event)
#        if manager.verify_database_connection(inform=True):
#            lne = manager._labnumber_entry_factory()
#            open_manager(event.window.application, lne)
#
##===============================================================================
# # Utilities
##===============================================================================
# class SignalCalculatorAction(ExperimentAction):
#    def perform(self, event):
#        obj = self._get_service(event, 'pychron.experiment.signal_calculator.SignalCalculator')
#        open_manager(event.window.application, obj)

# class OpenImportManagerAction(ExperimentAction):
#    accelerator = 'Ctrl+i'
#    def perform(self, event):
#        obj = self._get_service(event, 'pychron.experiment.import_manager.ImportManager')
#        open_manager(event.window.application, obj)
#
# class OpenExportManagerAction(ExperimentAction):
#    accelerator = 'Ctrl+Shift+e'
#    def perform(self, event):
#        obj = self._get_service(event, 'pychron.experiment.export_manager.ExportManager')
#        open_manager(event.window.application, obj)
#
# class OpenImageBrowserAction(ExperimentAction):
#    def perform(self, event):
#        browser = self._get_service(event, 'pychron.media_server.browser.MediaBrowser')
#        client = self._get_service(event, 'pychron.media_server.client.MediaClient')
#        browser.client = client
#        if browser.load_remote_directory('images'):
#            open_manager(event.window.application, browser)



# class AddProjectAction(Action):
#    def perform(self, event):
#        '''
#        '''
#        manager = _get_manager(event)
#
#
# class AddSampleProjectAction(Action):
#    def perform(self, event):
#        '''
#        '''
#        manager = _get_manager(event)
#
#
# class AddMaterialAction(Action):
#    def perform(self, event):
#        '''
#        '''
#        manager = _get_manager(event)
#
#
# class IrradiationChronologyAction(Action):
#    def perform(self, event):
#        '''
#        '''
#        manager = _get_manager(event)
#
#
# class IrradiationProductAction(Action):
#    def perform(self, event):
#        '''
#        '''
#        manager = _get_manager(event)


#============= EOF ====================================
