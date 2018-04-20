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
from __future__ import absolute_import
import os
import shutil

from git import Repo, GitCommandError

# ============= enthought library imports =======================
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import List, Str, Any, HasTraits, Bool, Instance, Int

# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_dir
from pychron.core.progress import progress_loader
from pychron.dvc.tasks import list_local_repos
from pychron.dvc.tasks.actions import CloneAction, AddBranchAction, CheckoutBranchAction, PushAction, PullAction, \
    FindChangesAction, LoadOriginAction, DeleteLocalChangesAction, ArchiveRepositoryAction
from pychron.dvc.tasks.panes import RepoCentralPane, SelectionPane
from pychron.envisage.tasks.base_task import BaseTask
# from pychron.git_archive.history import from_gitlog
from pychron.git.hosts import IGitHost
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.git_archive.utils import get_commits, ahead_behind
from pychron.github import Organization
from pychron.paths import paths


class RepoItem(HasTraits):
    name = Str
    dirty = Bool
    ahead = Int
    behind = Int
    status = Str

    def update(self, fetch=True):
        name = self.name
        p = os.path.join(paths.repository_dataset_dir, name)
        a, b = ahead_behind(p, fetch=fetch)
        self.ahead = a
        self.behind = b
        self.status = '{},{}'.format(a, b)


class ExperimentRepoTask(BaseTask):
    name = 'Experiment Repositories'

    selected_repository_name = Str
    selected_local_repository_name = Instance(RepoItem)

    repository_names = List

    local_names = List
    tool_bars = [SToolBar(CloneAction(),
                          AddBranchAction(),
                          CheckoutBranchAction(),
                          PushAction(),
                          PullAction(),
                          LoadOriginAction(),
                          FindChangesAction(),
                          DeleteLocalChangesAction(),
                          ArchiveRepositoryAction())]

    commits = List
    _repo = None
    selected_commit = Any
    branch = Str
    branches = List
    dvc = Any

    def activated(self):
        # self._preference_binder('pychron.dvc.connection', ('organization',))
        # prefid = 'pychron.dvc.connection'

        # bind_preference(self, 'favorites', '{}.favorites'.format(prefid))

        # self._preference_binder('pychron.github', ('oauth_token',))
        self.refresh_local_names()
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
        self.local_names = [RepoItem(name=i) for i in sorted(list_local_repos())]

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
            service = self.application.get_service(IGitHost)
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

    def load_origin(self):
        self.debug('load origin')
        self.repository_names = self.dvc.remote_repository_names()

    def delete_local_changes(self):
        self.info('delete local changes')
        name = self.selected_local_repository_name.name
        msg = 'Are you sure you want to delete your non-shared changes in "{}"'.format(name)
        if self.confirmation_dialog(msg):
            self._repo.delete_local_commits()
            self.selected_local_repository_name.dirty = False

    def create_central_pane(self):
        return RepoCentralPane(model=self)

    def create_dock_panes(self):
        return [SelectionPane(model=self)]

    def _refresh_branches(self):
        self.branches = self._repo.get_branch_names()
        b = self._repo.get_active_branch()

        force = self.branch == b
        self.branch = b
        if force:
            self._branch_changed(self.branch)

    def _selected_local_repository_name_changed(self, new):
        if new:
            root = os.path.join(paths.repository_dataset_dir, new.name)
            # print root, new, os.path.isdir(root)
            if os.path.isdir(root):
                repo = GitRepoManager()
                repo.open_repo(root)
                self._repo = repo
                self._refresh_branches()

    def _branch_changed(self, new):
        if new:
            # fmt = 'format:"%H|%cn|%ce|%ct|%s"'
            self.commits = get_commits(self._repo.active_repo, new, None, '')
            # self.commits = [from_gitlog(l) for l in self._repo.get_log(new, '--pretty={}'.format(fmt))]
        else:
            self.commits = []

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.repo.selection'))

# ============= EOF =============================================
