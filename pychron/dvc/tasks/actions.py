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
import os

from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.message_dialog import warning, information
from pyface.tasks.action.task_action import TaskAction
from traitsui.menu import Action

from pychron.core.ui.progress_dialog import myProgressDialog
from pychron.dvc import repository_path
from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import restart
from pychron.pychron_constants import DVC_PROTOCOL


class LocalRepositoryAction(TaskAction):
    enabled_name = 'selected_local_repository_name'


class RemoteRepositoryAction(TaskAction):
    enabled_name = 'selected_repository'


class CloneAction(RemoteRepositoryAction):
    method = 'clone'
    name = 'Clone'
    image = icon('repo-clone')
    tooltip = 'Clone repository from remote. e.g. git clone https://github.com...'


class AddBranchAction(LocalRepositoryAction):
    name = 'Add Branch'
    method = 'add_branch'
    image = icon('git-branch')
    tooltip = 'Add branch to selected repository'


class CheckoutBranchAction(LocalRepositoryAction):
    name = 'Checkout Branch'
    method = 'checkout_branch'
    image = icon('check')
    tooltip = 'Checkout branch. e.g. git checkout <branch_name>'


class PushAction(LocalRepositoryAction):
    name = 'Push'
    method = 'push'
    image = icon('repo-push')
    tooltip = 'Push changes to remote. git push'


class PullAction(LocalRepositoryAction):
    name = 'Pull'
    method = 'pull'
    image = icon('repo-pull')
    tooltip = 'Pull changes from remote. git pull'


class RebaseAction(LocalRepositoryAction):
    name = 'Rebase'
    method = 'rebase'
    image = icon('git-merge')
    tooltip = 'Rebase commits from [master] onto current branch. git rebase'


class FindChangesAction(LocalRepositoryAction):
    name = 'Find Changes'
    method = 'find_changes'
    tooltip = 'Search all local repositories for changes. e.g. git log <remote>/branch..HEAD'
    image = icon('search')


class DeleteLocalChangesAction(LocalRepositoryAction):
    name = 'Delete Local Changes'
    method = 'delete_local_changes'
    image = icon('trashcan')


class DeleteChangesAction(LocalRepositoryAction):
    name = 'Delete Commits'
    method = 'delete_commits'
    image = icon('trashcan')


class ArchiveRepositoryAction(LocalRepositoryAction):
    name = 'Archive Repository'
    method = 'archive_repository'
    image = icon('squirrel')


class LoadOriginAction(TaskAction):
    name = 'Load Origin'
    method = 'load_origin'
    image = icon('cloud-download')
    tooltip = 'Update the list of available repositories'


class SyncSampleInfoAction(LocalRepositoryAction):
    name = 'Sync Repo/DB Sample Info'
    method = 'sync_sample_info'
    tooltip = 'Copy information from Central Database to the selected repository'
    image = icon('octicon-database')


class SyncRepoAction(LocalRepositoryAction):
    name = 'Sync'
    method = 'sync_repo'
    tooltip = 'Sync to Origin. aka Pull then Push'
    image = icon('sync')


class RepoStatusAction(LocalRepositoryAction):
    name = 'Status'
    method = 'status'
    tooltip = 'Report the repository status. e.g. git status'
    image = icon('pulse')


class BookmarkAction(LocalRepositoryAction):
    name = 'Bookmark'
    method = 'add_bookmark'
    tooltip = 'Add a bookmark to the data reduction history. e.g. git tag -a <name> -m <message>'
    image = icon('git-bookmark')

# class SyncMetaDataAction(Action):
#     name = 'Sync Repo/DB Metadata'
#
#     def perform(self, event):
#         app = event.task.window.application
#         app.information_dialog('Sync Repo disabled')
#         return
#
#         dvc = app.get_service('pychron.dvc.dvc.DVC')
#         if dvc:
#             dvc.repository_db_sync('IR986', dry_run=False)


class ShareChangesAction(Action):
    name = 'Share Changes'

    def perform(self, event):
        from git import Repo
        from git.exc import InvalidGitRepositoryError
        from pychron.paths import paths
        remote = 'origin'
        branch = 'master'
        repos = []
        for d in os.listdir(paths.repository_dataset_dir):
            if d.startswith('.') or d.startswith('~'):
                continue

            try:
                r = Repo(repository_path(d))
            except InvalidGitRepositoryError:
                continue
            repos.append(r)

        n = len(repos)
        pd = myProgressDialog(max=n - 1,
                              can_cancel=True,
                              can_ok=False)
        pd.open()
        shared = False
        for r in repos:
            pd.change_message('Fetch {}'.format(os.path.basename(r.working_dir)))
            c = r.git.log('{}/{}..HEAD'.format(remote, branch), '--oneline')
            if c:

                r.git.pull()

                d = os.path.basename(r.working_dir)
                if confirm(None, 'Share changes made to {}.\n\n{}'.format(d, c)) == YES:
                    r.git.push(remote, branch)
                    shared = True

        msg = 'Changes successfully shared' if shared else 'No changes to share'
        information(None, msg)


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

class ClearCacheAction(Action):
    name = 'Clear Cache'

    def perform(self, event):
        app = event.task.window.application
        dvc = app.get_service(DVC_PROTOCOL)
        dvc.clear_cache()


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
        ret = confirm(None, 'You are now using the offline database. Restart now for changes to take effect')
        if ret == YES:
            restart()

# ============= EOF =============================================
