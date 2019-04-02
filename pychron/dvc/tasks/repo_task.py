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

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from git import GitCommandError, InvalidGitRepositoryError
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import List, Str, Any, HasTraits, Bool, Instance, Int, Event, Date, Property

# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.datetime_tools import format_iso_datetime
from pychron.core.helpers.filetools import unique_dir
from pychron.dvc import repository_path
from pychron.dvc.tasks import list_local_repos
from pychron.dvc.tasks.actions import CloneAction, AddBranchAction, CheckoutBranchAction, PushAction, PullAction, \
    FindChangesAction, LoadOriginAction, DeleteLocalChangesAction, ArchiveRepositoryAction, SyncSampleInfoAction, \
    SyncRepoAction, RepoStatusAction, BookmarkAction, RebaseAction, DeleteChangesAction
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
    create_date = Date
    push_date = Date

    def update(self, fetch=True):
        name = self.name
        p = repository_path(name)
        try:
            try:
                a, b = ahead_behind(p, fetch=fetch)
            except InvalidGitRepositoryError:
                return True

            self.ahead = a
            self.behind = b
            self.status = '{},{}'.format(a, b)
            self.refresh_needed = True
            return True
        except GitCommandError:
            pass


class ExperimentRepoTask(BaseTask, ColumnSorterMixin):
    name = 'Experiment Repositories'

    filter_repository_value = Str
    filter_origin_value = Str
    selected_repository = Instance(RepoItem)
    ncommits = Int(50, enter_set=True, auto_set=False)

    selected_local_repositories = List
    selected_local_repository_name = Property(depends_on='selected_local_repositories')#Instance(RepoItem)

    repository_names = List

    local_names = List
    tool_bars = [SToolBar(CloneAction(),
                          LoadOriginAction()),
                 SToolBar(AddBranchAction(),
                          CheckoutBranchAction(),
                          SyncRepoAction(),
                          PushAction(),
                          PullAction(),
                          RebaseAction(),
                          FindChangesAction(),
                          DeleteLocalChangesAction(),
                          ArchiveRepositoryAction(),
                          DeleteChangesAction(),
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
    o_origin_repos = None
    check_for_changes = Bool(True)
    origin_column_clicked = Any

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
        self.o_local_repos = None

    def find_changes(self, remote='origin', branch='master'):
        self.debug('find changes')

        # def func(item, prog, i, n):

        # def func(item, prog, i, n):
        #     name = item.name
        #     if prog:
        #         prog.change_message('Examining: {}({}/{})'.format(name, i, n))
        #     self.debug('examining {}'.format(name))
        #     r = Repo(repository_path(name))
        #     try:
        #         r.git.fetch()
        #         line = r.git.log('{}/{}..HEAD'.format(remote, branch), '--oneline')
        #         item.dirty = bool(line)
        #         item.update(fetch=False)
        #     except GitCommandError as e:
        #         self.warning('error examining {}. {}'.format(name, e))

        names = self.selected_local_repositories
        if not names:
            names = self.local_names

        self.dvc.find_changes(names, remote, branch)

        # progress_loader(names, func)
        self.local_names = sorted(self.local_names, key=lambda k: k.dirty, reverse=True)

    def rebase(self):
        self._repo.rebase()

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
        repo = self.selected_repository
        if not repo:
            self.warning_dialog('Please Select a repository to clone')
            return

        name = repo.name
        if name == 'meta':
            root = paths.dvc_dir
        else:
            root = paths.repository_dataset_dir

        path = os.path.join(root, name)
        if not os.path.isdir(path):
            self.debug('cloning repository {}'.format(name))
            service = self.dvc.application.get_service(IGitHost)
            service.clone_from(name, path, self.dvc.organization)
            self.refresh_local_names()
            msg = 'Repository "{}" successfully cloned'.format(name)
        else:
            msg = 'Repository "{}" already exists locally. Clone aborted '.format(name)

        self.information_dialog(msg)

    def add_branch(self):
        self.info('add branch')

        refresh = False
        commit = self.selected_commit
        if commit:
            if self._repo.create_branch(commit=commit.hexsha if commit else 'HEAD'):
                refresh = True
        else:
            name = None
            for r in self.selected_local_repositories:
                repo = self._get_repo(r.name)
                name = repo.create_branch(commit='HEAD', name=name, inform=False)
                if name is not None:
                    r.active_branch = repo.get_active_branch()
                    refresh = True

        if refresh:
            rs = ','.join((r.name for r in self.selected_local_repositories))
            self.information_dialog('Repositories "{}" now on branch "{}"'.format(rs, name))
            self._refresh_branches()

    def checkout_branch(self):
        branch = self.branch
        self.info('checkout branch {}'.format(branch))

        names = []
        for r in self.selected_local_repositories:
            r = self._get_repo(r.name)
            try:
                r.checkout_branch(branch, inform=False)
                r.active_branch = branch
                names.append(r.name)
            except BaseException:
                pass

        self.information_dialog('{} now on branch "{}'.format(names, branch))

    def load_origin(self):
        self.debug('load origin')
        self.repository_names = [RepoItem(name=r['name'],
                                          push_date=format_iso_datetime(r['pushed_at'], as_str=False),
                                          create_date=format_iso_datetime(r['created_at'], as_str=False))
                                 for r in self.dvc.remote_repositories()]
        self.o_origin_repos = None

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
                self.information_dialog('Sync complete')

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

    def delete_commits(self):
        selected = self._has_selected_local()
        if selected and self.selected_commit:
            hexsha = self.selected_commit.hexsha
            msg = 'Are you sure you want to permanently delete your changes in "{}"'.format(selected.name)
            if self.confirmation_dialog(msg):
                self._repo.delete_commits(hexsha)

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

    def _filter_origin_value_changed(self, new):
        if new:
            if self.o_origin_repos is None:
                self.o_origin_repos = self.repository_names

            self.repository_names = fuzzyfinder(new, self.o_origin_repos, attr='name')
        elif self.o_origin_repos:
            self.repository_names = self.o_origin_repos

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

    def _get_repo(self, name):
        root = repository_path(name)
        if os.path.isdir(root):
            repo = GitRepoManager()
            repo.open_repo(root)

            return repo

    def _get_selected_local_repository_name(self):
        if self.selected_local_repositories:
            return self.selected_local_repositories[0]

    def _selected_local_repositories_changed(self, new):
        if new:
            repo = self._get_repo(new[0].name)
            if repo:
                self._repo = repo
                self._refresh_branches()
                self._refresh_tags()

    def _get_commits(self, new):
        if new:
            self.commits = get_commits(self._repo.active_repo, new, None, '', limit=self.ncommits)
        else:
            self.commits = []

    def _ncommits_changed(self):
        self._get_commits(self.branch)

    def _branch_changed(self, new):
        self._get_commits(new)

    def _origin_column_clicked_changed(self, event):
        self._column_clicked_handled(event)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.repo.selection'))

# ============= EOF =============================================
