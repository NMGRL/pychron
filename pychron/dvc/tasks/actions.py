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
from pyface.tasks.action.task_action import TaskAction
from traitsui.menu import Action

from pychron.envisage.resources import icon


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


class PullAnalysesAction(Action):
    name = 'Pull Analyses'
    image = icon('arrow_down')

    def perform(self, event):
        pass
        # from pychron.envisage.browser.view import StandaloneBrowserView
        # from pychron.dvc.offline_index import index_factory
        # app = event.task.window.application
        #
        # db = index_factory(paths.index_db)
        #
        # dvc = app.get_service('pychron.dvc.dvc.DVC')
        # dvc.initialize()
        # bmodel = app.get_service('pychron.envisage.browser.browser_model.BrowserModel')
        # bmodel.activated()
        # bmodel.activate_sample_browser()
        # browser_view = StandaloneBrowserView(model=bmodel)
        # info = browser_view.edit_traits(kind='livemodal')
        #
        # if info.result:
        #     records = bmodel.get_analysis_records()
        #     if records:
        #         analyses = dvc.make_analyses(records)
        #
        #         def func(x, prog, i, n):
        #             if prog:
        #                 prog.change_message('Adding to Index: {}'.format(x.record_id))
        #             db.add_analysis_to_index(x.experiment_identifier, x)
        #
        #         progress_iterator(analyses, func, threshold=1)

# ============= EOF =============================================
