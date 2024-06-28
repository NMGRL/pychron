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
from operator import attrgetter

from apptools.preferences.preference_binding import bind_preference
from git import GitCommandError, InvalidGitRepositoryError
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import (
    List,
    Str,
    Any,
    HasTraits,
    Bool,
    Instance,
    Int,
    Event,
    Date,
    Property,
    Button,
)

# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.datetime_tools import format_iso_datetime
from pychron.core.helpers.filetools import unique_dir
from pychron.dvc import repository_path, UUID_RE
from pychron.dvc.tasks import list_local_repos
from pychron.dvc.tasks.actions import (
    CloneAction,
    AddBranchAction,
    CheckoutBranchAction,
    PushAction,
    PullAction,
    FindChangesAction,
    LoadOriginAction,
    DeleteLocalChangesAction,
    ArchiveRepositoryAction,
    SyncSampleInfoAction,
    SyncRepoAction,
    RepoStatusAction,
    BookmarkAction,
    RebaseAction,
    DeleteChangesAction,
    SortLocalReposAction,
    RevertCommitAction,
    MergeAction,
)
from pychron.dvc.tasks.branch_merge_view import BranchMergeView
from pychron.dvc.tasks.panes import RepoCentralPane, SelectionPane
from pychron.envisage.tasks.base_task import BaseTask

# from pychron.git_archive.history import from_gitlog
from pychron.git.hosts import IGitHost
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.git_archive.utils import ahead_behind, get_tags
from pychron.git_archive.views import CommitFactory
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR, STARTUP_MESSAGE_POSITION
from pychron.regex import RUNID_PATH_REGEX, TAG_PATH_REGEX


class DiffItem(HasTraits):
    addition = Str
    subtraction = Str

    @property
    def complete(self):
        return self.addition and self.subtraction


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
            self.status = "{},{}".format(a, b)
            self.refresh_needed = True
            return True
        except GitCommandError:
            pass


class ExperimentRepoTask(BaseTask, ColumnSorterMixin):
    id = "pychron.repo.task"
    name = "Repositories"

    filter_repository_value = Str
    filter_origin_value = Str
    selected_repository = Instance(RepoItem)
    ncommits = Int(30, enter_set=True, auto_set=False)
    use_simplify_dag = Bool(False)

    selected_local_repositories = List
    selected_local_repository_name = Property(
        depends_on="selected_local_repositories"
    )  # Instance(RepoItem)

    repository_names = List

    local_names = List
    tool_bars = [
        SToolBar(CloneAction(), LoadOriginAction()),
        SToolBar(
            AddBranchAction(),
            CheckoutBranchAction(),
            SyncRepoAction(),
            PushAction(),
            PullAction(),
            MergeAction(),
            # RebaseAction(),
            FindChangesAction(),
            DeleteLocalChangesAction(),
            ArchiveRepositoryAction(),
            DeleteChangesAction(),
            RevertCommitAction(),
            RepoStatusAction(),
            BookmarkAction(),
            SortLocalReposAction(),
        ),
        SToolBar(SyncSampleInfoAction()),
    ]

    selected = List
    commits = List
    scroll_to_row = Int
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
    auto_fetch = Bool(False)
    refresh_branch_button = Button

    files = List
    selected_file = Str
    analyses = List
    diff_text = Str
    diffs = List

    def activated(self):
        bind_preference(
            self, "check_for_changes", "pychron.dvc.repository.check_for_changes"
        )
        bind_preference(self, "auto_fetch", "pychron.dvc.repository.auto_fetch")
        self.refresh_local_names()
        if self.check_for_changes:
            if self.confirmation_dialog(
                "Check all Repositories for changes", position=STARTUP_MESSAGE_POSITION
            ):
                self.find_changes()

    def sort_repos(self):
        names = self.selected_local_repositories
        if not names:
            names = self.local_names

        sorted_names = [
            r[0] for r in self.dvc.sorted_repositories([r.name for r in names])
        ]

        for si in reversed(sorted_names):
            lr = next((r for r in names if r.name == si))
            self.local_names.insert(0, lr)

    def archive_repository(self):
        name, dst = self._archive_repository()

        self.refresh_local_names()
        self.information_dialog('"{}" Successfully archived to {}'.format(name, dst))

    def refresh_local_names(self):
        self.local_names = [
            RepoItem(name=i, active_branch=branch)
            for i, branch in sorted(list_local_repos())
        ]
        self.o_local_repos = None

    def find_changes(self, names=None, remote="origin", branch="master"):
        self.debug("find changes. names={}".format(names))
        if names:
            names = [n for n in self.local_names if n.name in names]
        else:
            names = self.selected_local_repositories
            if not names:
                names = self.local_names
        self.dvc.find_changes(names, remote, branch)

        # progress_loader(names, func)
        self.local_names = sorted(self.local_names, key=lambda k: k.dirty, reverse=True)

    def rebase(self):
        self._repo.rebase()

    def merge(self):
        if self._repo.smart_pull(quiet=False):
            bmv = BranchMergeView(
                repo=self._repo,
                to_=self.branch,
                branches=[
                    b
                    for b in self.branches
                    if not b.startswith("origin") and b != self.branch
                ],
            )

            info = bmv.edit_traits()
            if info.result and bmv.from_:
                if self.confirmation_dialog("Are you sure you want to merge?"):
                    self.debug("merge {} into {}".format(bmv.from_, bmv.to_))
                    self._repo.merge(bmv.from_)
                    self.find_changes(names=[self.selected_local_repository_name])

    def pull(self):
        self._repo.smart_pull(quiet=False)
        self.find_changes(names=[self.selected_local_repository_name.name])

    def push(self):
        if not self._repo.has_remote():
            from pychron.dvc.tasks.add_remote_view import AddRemoteView

            a = AddRemoteView()
            info = a.edit_traits(kind="livemodal")
            if info.result:
                if a.url and a.name:
                    self._repo.create_remote(a.url, a.name)
                    self._repo.push(remote=a.name, inform=True)
        else:
            self.dvc.push_repository(self._repo, inform=True)

        self.find_changes(names=(self._repo.name,))
        self.selected_local_repository_name.dirty = False

    def clone(self):
        repo = self.selected_repository
        if not repo:
            self.warning_dialog("Please Select a repository to clone")
            return

        name = repo.name
        if name == "meta":
            root = paths.dvc_dir
        else:
            root = paths.repository_dataset_dir

        path = os.path.join(root, name)
        if not os.path.isdir(path):
            self.debug("cloning repository {}".format(name))
            service = self.dvc.application.get_service(IGitHost)
            service.clone_from(name, path, self.dvc.organization)
            self.refresh_local_names()
            msg = 'Repository "{}" successfully cloned'.format(name)
        else:
            msg = 'Repository "{}" already exists locally. Clone aborted '.format(name)

        self.information_dialog(msg)

    def add_branch(self):
        self.info("add branch")

        refresh = False
        commit = self.selected_commit
        if commit:
            if self._repo.create_branch(commit=commit.hexsha if commit else "HEAD"):
                refresh = True
        else:
            name = None
            for r in self.selected_local_repositories:
                repo = self._get_repo(r.name)
                name = repo.create_branch(commit="HEAD", name=name, inform=False)
                if name is not None:
                    r.active_branch = repo.get_active_branch()
                    refresh = True

        if refresh:
            rs = ",".join((r.name for r in self.selected_local_repositories))
            self.information_dialog(
                'Repositories "{}" now on branch "{}"'.format(rs, name)
            )
            self._refresh_branches()

    def checkout_branch(self):
        branch = self.branch
        self.info("checkout branch {}".format(branch))

        names = []
        for r in self.selected_local_repositories:
            r = self._get_repo(r.name)
            try:
                r.checkout_branch(branch, inform=False)
                r.active_branch = branch
                names.append(r.name)
            except BaseException:
                self.debug_exception()
                self.warning("failed checking out {}, branch={}".format(r.name, branch))

        self.information_dialog('{} now on branch "{}"'.format(",".join(names), branch))

    def load_origin(self):
        self.debug("load origin")
        self.repository_names = [
            RepoItem(
                name=r["name"],
                push_date=format_iso_datetime(r.get("pushed_at"), as_str=False),
                create_date=format_iso_datetime(r.get("created_at"), as_str=False),
            )
            for r in self.dvc.remote_repositories()
        ]
        self.o_origin_repos = None

    def delete_local_changes(self):
        self.info("delete local changes")
        selected = self._has_selected_local()
        if selected:
            name = selected.name
            msg = 'Are you sure you want to delete your non-shared changes in "{}"'.format(
                name
            )
            if self.confirmation_dialog(msg):
                self._repo.delete_local_commits()
                self.selected_local_repository_name.dirty = False

    def sync_sample_info(self):
        self.info("sync sample info")

        selected = self._has_selected_local()
        if selected:
            name = selected.name
            if self.confirmation_dialog(
                "Are you sure you want to copy values from the "
                'database into the repository "{}"'.format(name)
            ):
                self.dvc.repository_db_sync(name)
                self.information_dialog("Sync complete")

    def sync_repo(self):
        selected = self._has_selected_local()
        if selected:
            if self.confirmation_dialog(
                "Are you sure you want to Sync to Origin. aka Pull/Push"
            ):
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
                    self.dvc.add_bookmark(
                        selected.name,
                        nt.name,
                        nt.message or "No message provided",
                        hexsha=hexsha,
                    )
                else:
                    self.warning_dialog(
                        "A name is required to add a bookmark. Please try again"
                    )

    def revert_selected_commit(self):
        selected = self._has_selected_local()
        if selected and self.selected_commit:
            hexsha = self.selected_commit.hexsha
            self._repo.revert_commit(hexsha)

    def delete_commits(self):
        selected = self._has_selected_local()
        if selected and self.selected_commit:
            hexsha = self.selected_commit.hexsha
            msg = (
                'Are you sure you want to permanently delete your changes in "{}". This will delete all '
                "changes later than the selected row. "
                'To undo an individual commit use "Revert Selected Commit"'.format(
                    selected.name
                )
            )
            if self.confirmation_dialog(msg):
                self._archive_repository(move=False)
                self._repo.delete_commits(hexsha)

    # task
    def create_central_pane(self):
        return RepoCentralPane(model=self)

    def create_dock_panes(self):
        return [SelectionPane(model=self)]

    # private
    def _archive_repository(self, src=None, move=True):
        if src is None:
            src = self._repo.path
        self.debug("archive repository")

        root = os.path.join(paths.dvc_dir, "archived_repositories")
        if not os.path.isdir(root):
            os.mkdir(root)

        name = os.path.basename(src)
        dst = unique_dir(root, name, make=False)
        func = shutil.move if move else shutil.copytree
        func(self._repo.path, dst)
        return name, dst

    def _refresh_tags(self):
        self.git_tags = get_tags(self._repo.active_repo)

    def _refresh_branches(self, fetch=False):
        self.debug("refresh branches fetch={}".format(fetch))
        if self.auto_fetch or fetch:
            self._repo.fetch()

        self.branches = [NULL_STR] + self._repo.get_branch_names()
        b = self._repo.get_active_branch()

        force = self.branch == b
        self.branch = b
        if force:
            self._branch_changed(self.branch)

        self.selected_local_repository_name.active_branch = b

    def _has_selected_local(self):
        if not self.selected_local_repository_name:
            self.information_dialog("Please select a local repository")
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

    def _get_commits(self, new):
        if new:
            cs = self._repo.get_dag(
                branch=new, limit=self.ncommits, simplify=self.use_simplify_dag
            )
            CommitFactory.reset()
            cs = [CommitFactory.new(log_entry=ci) for ci in cs.split("\n")]
            self.commits = sorted(cs, reverse=True, key=attrgetter("authdate"))
        else:
            self.commits = []

    def _set_files(self):
        c = self.selected_commit
        fs = []
        if c:
            fs = self._repo.get_modified_files(self.selected_commit.oid)

        self._set_analyses(fs)
        self.files = fs

    def _set_analyses(self, fs):
        def func(fx, m):
            tag = m.group("tag")
            if tag:
                fx = fx.replace(tag, "")
                fx, _ = os.path.splitext(fx)

            fx = fx.replace("/", "")
            fx, _ = os.path.splitext(fx)
            return fx

        ans = []
        uuids = []
        for fi in fs:
            m = RUNID_PATH_REGEX.match(fi)
            if m:
                ans.append((fi, m))
                continue

            m = TAG_PATH_REGEX.match(fi)
            if m:
                head = m.group("head")
                tail = m.group("tail")
                uuids.append("{}{}".format(head, tail))
                continue

        ans = list({an for an in (func(*a) for a in ans) if an})

        nans = []
        for ai in ans:
            if UUID_RE.match(ai):
                uuids.append(ai)
            else:
                nans.append(ai)

        self.analyses = sorted(nans + self.dvc.convert_uuid_runids(uuids))

    def _make_diff_changes(self, rev, d):
        rev = self._repo.get_commit(rev)
        print("asdf", d)
        if d.change_type == "A":
            print(rev.stats)
        elif d.change_type == "M":
            pass
        # txt = self._repo.diff('{}~1'.format(oid), oid, '--', new)
        # ds = []
        # item = None
        # for line in txt.split('\n'):
        #     pass
        # if line[:2] == '- ':
        #     if item is None:
        #         item = DiffItem()
        #     item.subtraction = line[2:]
        # elif line[:2] == '+ ':
        #     if item is None:
        #         item = DiffItem()
        #     item.addition = line[2:]
        #
        # if item and item.complete:
        #     ds.append(item)
        #     item = None

        # ds = []
        # d = ''
        # ds.append(d)
        # self.diffs = ds

    # handlers
    def _refresh_branch_button_changed(self):
        selected = self._has_selected_local()
        if selected:
            self._refresh_branches(fetch=True)

    def _selected_file_changed(self, new):
        if new:
            oid = self.selected_commit.oid

            a = "{}~1".format(oid)
            b = oid

            # txt = self._repo.diff('-U0', '{}~1'.format(oid), oid, '--', new)
            # self.diff_text = txt
            # self._make_diff_changes(txt)

            d = self._repo.odiff(a, b, paths=new)[0]
            self.diff_text = d.diff
            self._make_diff_changes(a, d)
        else:
            self.diffs = []
            self.diff_text = ""

    def _selected_changed(self, new):
        if new:
            self.selected_commit = new[0]
            # i = next((i for i, c in enumerate(self.commits)))
            self.scroll_to_row = self.commits.index(self.selected_commit)
        self._set_files()

    def _selected_commit_changed(self, new):
        self._set_files()

    def _filter_origin_value_changed(self, new):
        if new:
            if self.o_origin_repos is None:
                self.o_origin_repos = self.repository_names

            self.repository_names = fuzzyfinder(new, self.o_origin_repos, attr="name")
        elif self.o_origin_repos:
            self.repository_names = self.o_origin_repos

    def _filter_repository_value_changed(self, new):
        if new:
            if self.o_local_repos is None:
                self.o_local_repos = self.local_names

            self.local_names = fuzzyfinder(new, self.o_local_repos, attr="name")
        elif self.o_local_repos:
            self.local_names = self.o_local_repos

    def _selected_local_repositories_changed(self, new):
        if new:
            repo = self._get_repo(new[0].name)
            if repo:
                self._repo = repo
                self._refresh_branches()
                self._refresh_tags()

    def _use_simplify_dag_changed(self):
        self._get_commits(self.branch)

    def _ncommits_changed(self):
        self._get_commits(self.branch)

    def _branch_changed(self, new):
        self._get_commits(new)

    def _origin_column_clicked_changed(self, event):
        self._column_clicked_handled(event)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("pychron.repo.selection"))


# ============= EOF =============================================
