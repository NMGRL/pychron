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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.message_dialog import information, warning
from pyface.tasks.action.task_action import TaskAction
from traitsui.menu import Action

from pychron.envisage.resources import icon
from pychron.pychron_constants import DVC_PROTOCOL


class LocalRepositoryAction(TaskAction):
    enabled_name = 'selected_local_repository_name'


class RemoteRepositoryAction(TaskAction):
    enabled_name = 'selected_repository_name'


class CloneAction(RemoteRepositoryAction):
    method = 'clone'
    name = 'Clone'


class AddBranchAction(LocalRepositoryAction):
    name = 'Add Branch'
    method = 'add_branch'
    image = icon('add')


class CheckoutBranchAction(LocalRepositoryAction):
    name = 'Checkout Branch'
    method = 'checkout_branch'
    image = icon('checkout')


class PushAction(LocalRepositoryAction):
    name = 'Push'
    method = 'push'
    image = icon('arrow_up')


class PullAction(LocalRepositoryAction):
    name = 'Pull'
    method = 'pull'
    image = icon('arrow_down')


# class PullAnalysesAction(Action):
#     name = 'Pull Analyses'
#     image = icon('arrow_down')
#
#     def perform(self, event):
#         from pychron.envisage.browser.view import StandaloneBrowserView
#         from pychron.dvc.offline_index import index_factory
#
#         app = event.task.window.application
#
#         db = index_factory(paths.index_db)
#
#         dvc = app.get_service('pychron.dvc.dvc.DVC')
#         dvc.initialize()
#
#         bserivce = 'pychron.envisage.browser.browser_model.BrowserModel'
#         bmodel = app.get_service(bserivce)
#
#         bmodel.activated()
#         bmodel.activate_sample_browser()
#         browser_view = StandaloneBrowserView(model=bmodel)
#         info = browser_view.edit_traits(kind='livemodal')
#
#         if info.result:
#             records = bmodel.get_analysis_records()
#             if records:
#                 analyses = dvc.make_analyses(records)
#
#                 def func(x, prog, i, n):
#                     if prog:
#                         prog.change_message(
#                                 'Adding to Index: {}'.format(x.record_id))
#                     db.add_analysis_to_index(x.experiment_identifier, x)
#
#                 progress_iterator(analyses, func, threshold=1)


class WorkOfflineAction(Action):
    name = 'Work Offline'

    def perform(self, event):
        app = event.task.window.application
        dvc = app.get_service(DVC_PROTOCOL)

        if dvc.db.kind != 'mysql':
            warning(None, 'Your are not using a centralized MySQL database')
        else:
            from pychron.dvc.work_offline import WorkOffline
            wo = WorkOffline(dvc=dvc, application=app)
            if wo.initialize():
                wo.edit_traits()


class UseOfflineDatabase(Action):
    name = 'Use Offline Database'

    def perform(self, event):
        from pychron.dvc.work_offline import switch_to_offline_database
        app = event.task.window.application
        switch_to_offline_database(app.preferences)
        information(None, 'You are now using the offline database. Restart for changes to take effect')

# ============= EOF =============================================
