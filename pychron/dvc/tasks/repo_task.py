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

# ============= standard library imports ========================
import os
import shutil

from apptools.preferences.preference_binding import bind_preference
from git import Repo, GitCommandError
# ============= enthought library imports =======================
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import List, Str, Any, HasTraits, Bool, Instance, Int, Event

# ============= local library imports  ==========================
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.filetools import unique_dir
from pychron.core.progress import progress_loader
from pychron.dvc.tasks import list_local_repos
from pychron.dvc.tasks.actions import CloneAction, AddBranchAction, CheckoutBranchAction, PushAction, PullAction, \
    FindChangesAction, LoadOriginAction, DeleteLocalChangesAction, ArchiveRepositoryAction, SyncSampleInfoAction, \
    SyncRepoAction, RepoStatusAction, BookmarkAction
from pychron.dvc.tasks.panes import RepoCentralPane, SelectionPane
from pychron.envisage.tasks.base_task import BaseTask
# from pychron.git_archive.history import from_gitlog
from pychron.git.hosts import IGitHost
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.git_archive.utils import get_commits, ahead_behind, get_tags
from pychron.paths import paths


class RepoItem(HasTraits):
    name = Str
    dirty = Bool
    ahead = Int
    behind = Int
    status = Str
    refresh_needed = Event
    active_branch = Str

    def update(self, fetch=True):
        name = self.name
        p = os.path.join(paths.repository_dataset_dir, name)
        a, b = ahead_behind(p, fetch=fetch)
        self.ahead = a
        self.behind = b
        self.status = '{},{}'.format(a, b)
        self.refresh_needed = True


class ExperimentRepoTask(BaseTask):
    name = 'Experiment Repositories'

    filter_repository_value = Str
    selected_repository_name = Str
    selected_local_repository_name = Instance(RepoItem)

    repository_names = List

    local_names = List
    tool_bars = [SToolBar(CloneAction(),
                          LoadOriginAction()),
                 SToolBar(AddBranchAction(),
                          CheckoutBranchAction(),
                          SyncRepoAction(),
                          PushAction(),
                          PullAction(),
                          FindChangesAction(),
                          DeleteLocalChangesAction(),
                          ArchiveRepositoryAction(),
                          RepoStatusAction(),
                          BookmarkAction()),
                 SToolBar(SyncSampleInfoAction())]

    commits = List
    git_tags = List
    _repo = None
    selected_commit = Any
    branch = Str
    branches = List
    dvc = Any
    o_local_repos = None
    check_for_changes = Bool(True)

    def activated(self):
        bind_preference(self, 'check_for_changes', 'pychron.dvc.repository.check_for_changes')
        # self._preference_binder('pychron.dvc.connection', ('organization',))
        # prefid = 'pychron.dvc.connection'

        # bind_preference(self, 'favorites', '{}.favorites'.format(prefid))

        # self._preference_binder('pychron.github', ('oauth_token',))
        self.refresh_local_names()
        if self.check_for_changes:
            if self.confirmation_dialog('Check all Repositories for changes'):
                self.find_changes()

    def archive_repository(self):
        self.debug('archive repository')

        root = os.path.join(paths.dvc_dir, 'archived_repositories')
        if not os.path.isdir(root):
            os.mkdir(root)

        src = self._repo.path
        name = os.path.basename(src)
        dst = unique_dir(root, name, make=False)
        shutil.move(self._repo.path, dst)
        self.refresh_local_names()
        self.information_dialog('"{}" Successfully archived to {}'.format(name, dst))

    def refresh_local_names(self):
        self.local_names = [RepoItem(name=i, active_branch=branch) for i, branch in sorted(list_local_repos())]

    def find_changes(self, remote='origin', branch='master'):
        self.debug('find changes')

        def func(item, prog, i, n):
            name = item.name
            if prog:
                prog.change_message('Examining: {}({}/{})'.format(name, i, n))
            self.debug('examining {}'.format(name))
            r = Repo(os.path.join(paths.repository_dataset_dir, name))
            try:
                r.git.fetch()
                line = r.git.log('{}/{}..HEAD'.format(remote, branch), '--oneline')
                item.dirty = bool(line)
            except GitCommandError as e:
                self.warning('error examining {}. {}'.format(name, e))

        if self.selected_local_repository_name:
            names = (self.selected_local_repository_name,)
        else:
            names = self.local_names

        progress_loader(names, func)
        self.local_names = sorted(self.local_names, key=lambda k: k.dirty, reverse=True)

    def pull(self):
        self._repo.smart_pull(quiet=False)

    def push(self):
        if not self._repo.has_remote():
            from pychron.dvc.tasks.add_remote_view import AddRemoteView

            a = AddRemoteView()
            info = a.edit_traits(kind='livemodal')
            if info.result:
                if a.url and a.name:
                    self._repo.create_remote(a.url, a.name)
                    self._repo.push(remote=a.name, inform=True)
        else:
            self._repo.push(inform=True)

        self.selected_local_repository_name.dirty = False

    def clone(self):
        name = self.selected_repository_name
        if name == 'meta':
            root = paths.dvc_dir
        else:
            root = paths.repository_dataset_dir

        path = os.path.join(root, name)
        if not os.path.isdir(path):
            self.debug('cloning repository {}'.format(name))
            service = self.dvc.application.get_service(IGitHost)
            service.clone_from(name, path, self.organization)
            self.refresh_local_names()

    def add_branch(self):
        self.info('add branch')
        commit = self.selected_commit

        if self._repo.create_branch(commit=commit.hexsha if commit else 'HEAD'):
            self._refresh_branches()

    def checkout_branch(self):
        self.info('checkout branch {}'.format(self.branch))
        self._repo.checkout_branch(self.branch)
        self.selected_local_repository_name.active_branch = self.branch

    def load_origin(self):
        self.debug('load origin')
        self.repository_names = self.dvc.remote_repository_names()

    def delete_local_changes(self):
        self.info('delete local changes')
        selected = self._has_selected_local()
        if selected:
            name = selected.name
            msg = 'Are you sure you want to delete your non-shared changes in "{}"'.format(name)
            if self.confirmation_dialog(msg):
                self._repo.delete_local_commits()
                self.selected_local_repository_name.dirty = False

    def sync_sample_info(self):
        self.info('sync sample info')

        selected = self._has_selected_local()
        if selected:
            name = selected.name
            if self.confirmation_dialog('Are you sure you want to copy values from the '
                                        'database into the repository "{}"'.format(name)):
                self.dvc.repository_db_sync(name)

    def sync_repo(self):
        selected = self._has_selected_local()
        if selected:
            if self.confirmation_dialog('Are you sure you want to Sync to Origin. aka Pull/Push'):
                self.pull()
                self.push()

    def status(self):
        selected = self._has_selected_local()
        if selected:
            self.dvc.status_view(selected.name)

    def add_bookmark(self):
        selected = self._has_selected_local()
        if selected:
            hexsha = None
            if self.selected_commit:
                hexsha = self.selected_commit.hexsha

            from pychron.git_archive.views import NewTagView
            nt = NewTagView()
            info = nt.edit_traits()
            if info.result:
                if nt.name:
                    self.dvc.add_bookmark(selected.name, nt.name,
                                          nt.message or 'No message provided',
                                          hexsha=hexsha)
                else:
                    self.warning_dialog('A name is required to add a bookmark. Please try again')

    # task
    def create_central_pane(self):
        return RepoCentralPane(model=self)

    def create_dock_panes(self):
        return [SelectionPane(model=self)]

    # private
    def _refresh_tags(self):
        self.git_tags = get_tags(self._repo.active_repo)

    def _refresh_branches(self):
        self.branches = self._repo.get_branch_names()
        b = self._repo.get_active_branch()

        force = self.branch == b
        self.branch = b
        if force:
            self._branch_changed(self.branch)

        self.selected_local_repository_name.active_branch = b

    def _filter_repository_value_changed(self, new):
        if new:
            if self.o_local_repos is None:
                self.o_local_repos = self.local_names

            self.local_names = fuzzyfinder(new, self.o_local_repos, attr='name')
        elif self.o_local_repos:
            self.local_names = self.o_local_repos

    def _has_selected_local(self):
        if not self.selected_local_repository_name:
            self.information_dialog('Please select a local repository')
            return

        return self.selected_local_repository_name

    def _selected_local_repository_name_changed(self, new):
        if new:
            root = os.path.join(paths.repository_dataset_dir, new.name)
            # print root, new, os.path.isdir(root)
            if os.path.isdir(root):
                repo = GitRepoManager()
                repo.open_repo(root)
                self._repo = repo
                self._refresh_branches()
                self._refresh_tags()

    def _branch_changed(self, new):
        if new:
            self.commits = get_commits(self._repo.active_repo, new, None, '')
        else:
            self.commits = []

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.repo.selection'))

# ============= EOF =============================================
