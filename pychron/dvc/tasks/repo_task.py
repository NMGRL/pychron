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
from git import Repo, GitCommandError

# ============= enthought library imports =======================
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import List, Str, Any, HasTraits, Bool, Instance, Int

# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.dvc.tasks.actions import CloneAction, AddBranchAction, CheckoutBranchAction, PushAction, PullAction, \
    FindChangesAction
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
    organization = Str
    oauth_token = Str

    local_names = List
    tool_bars = [SToolBar(CloneAction(),
                          AddBranchAction(),
                          CheckoutBranchAction(),
                          PushAction(),
                          PullAction(),
                          FindChangesAction())]

    commits = List
    _repo = None
    selected_commit = Any
    branch = Str
    branches = List

    def activated(self):
        self._preference_binder('pychron.dvc', ('organization',))
        self._preference_binder('pychron.github', ('oauth_token',))
        org = Organization(self.organization)
        org._oauth_token = self.oauth_token

        self.refresh_local_names()
        if self.confirmation_dialog('Check all Repositories for changes'):
            self.find_changes()

        self.repository_names = org.repo_names

    def refresh_local_names(self):
        self.local_names = [RepoItem(name=i) for i in sorted(self.list_repos())]

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
            except GitCommandError, e:
                self.warning('error examining {}. {}'.format(name, e))

        if self.selected_local_repository_name:
            names = (self.selected_local_repository_name,)
        else:
            names = self.local_names

        progress_loader(names, func)
        self.local_names = sorted(self.local_names, key=lambda k: k.dirty, reverse=True)

    def list_repos(self):
        for i in os.listdir(paths.repository_dataset_dir):
            if i.startswith('.'):
                continue
            elif i.startswith('~'):
                continue

            d = os.path.join(paths.repository_dataset_dir, i)
            if os.path.isdir(d):
                gd = os.path.join(d, '.git')
                if os.path.isdir(gd):
                    yield i

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
                    self._repo.push(remote=a.name)
        else:
            self._repo.push()

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
