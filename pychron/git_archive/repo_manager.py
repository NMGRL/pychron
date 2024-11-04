# ===============================================================================
# Copyright 2013 Jake Ross
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
import hashlib
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

import git
from git import Repo
from git.exc import GitCommandError
from traits.api import Any, Str, List, Event

from pychron.core.helpers.filetools import fileiter
from pychron.core.progress import open_progress
from pychron.envisage.view_util import open_view
from pychron.git_archive.diff_view import DiffView, DiffModel
from pychron.git_archive.git_objects import GitSha
from pychron.git_archive.history import BaseGitHistory
from pychron.git_archive.merge_view import MergeModel, MergeView
from pychron.git_archive.utils import get_head_commit, ahead_behind, from_gitlog, LOGFMT
from pychron.git_archive.views import NewBranchView
from pychron.loggable import Loggable
from pychron.pychron_constants import DATE_FORMAT, NULL_STR
from pychron.updater.commit_view import CommitView
from pychron.globals import globalv


def get_repository_branch(path):
    r = Repo(path)
    b = r.active_branch
    return b.name


def grep(arg, name):
    process = subprocess.Popen(["grep", "-lr", arg, name], stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr


def format_date(d):
    return time.strftime("%m/%d/%Y %H:%M", time.gmtime(d))


def isoformat_date(d):
    if isinstance(d, (float, int)):
        d = datetime.fromtimestamp(d)

    return d.strftime(DATE_FORMAT)
    # return time.mktime(time.gmtime(d))


class StashCTX(object):
    def __init__(self, repo):
        self._repo = repo
        self._error = None

    def __enter__(self):
        try:
            self._repo.git.stash()
        except GitCommandError as e:
            self._error = e
            return e

    def __exit__(self, *args, **kw):
        if not self._error:
            try:
                self._repo.git.stash("pop")
            except GitCommandError:
                pass


class GitRepoManager(Loggable):
    """
    manage a local git repository

    """

    _repo = Any
    # root=Directory
    path = Str
    selected = Any
    selected_branch = Str
    selected_path_commits = List
    selected_commits = List
    refresh_commits_table_needed = Event
    path_dirty = Event
    remote = Str
    pathname = Str

    def set_name(self, p):
        self.name = "{}<GitRepo>".format(os.path.basename(p))

    def open_repo(self, name, root=None):
        """
        name: name of repo
        root: root directory to create new repo
        """
        if root is None:
            p = name
        else:
            p = os.path.join(root, name)

        self.path = p

        self.set_name(p)

        if os.path.isdir(p):
            self.init_repo(p)
            return True
        else:
            os.mkdir(p)
            repo = Repo.init(p)
            self.debug("created new repo {}".format(p))
            self._repo = repo
            return False

    def init_repo(self, path):
        """
        path: absolute path to repo

        return True if git repo exists
        """
        if os.path.isdir(path):
            g = os.path.join(path, ".git")
            if os.path.isdir(g):
                self._repo = Repo(path)
                self.set_name(path)
                return True
            else:
                self.debug("{} is not a valid repo. Initializing now".format(path))
                self._repo = Repo.init(path)
                self.set_name(path)

    def delete_local_commits(self, remote="origin", branch=None):
        if branch is None:
            branch = self._repo.active_branch.name

        self._repo.git.reset("--hard", "{}/{}".format(remote, branch))

    def delete_commits(self, hexsha, remote="origin", branch=None, push=True):
        if branch is None:
            branch = self._repo.active_branch.name

        self._repo.git.reset("--hard", hexsha)
        if push:
            self._repo.git.push(remote, branch, "--force")

    def add_paths_explicit(self, apaths):
        self.index.add(apaths)

    def add_paths(self, apaths):
        if not isinstance(apaths, (list, tuple)):
            apaths = (apaths,)

        changes = self.get_local_changes(change_type=("A", "R", "M"))
        changes = [os.path.join(self.path, c) for c in changes]
        if changes:
            self.debug("-------- local changes ---------")
            for c in changes:
                self.debug(c)

        deletes = self.get_local_changes(change_type=("D",))
        if deletes:
            self.debug("-------- deletes ---------")
            for c in deletes:
                self.debug(c)

        untracked = self.untracked_files()
        if untracked:
            self.debug("-------- untracked paths --------")
            for t in untracked:
                self.debug(t)

        changes.extend(untracked)

        self.debug("add paths {}".format(apaths))

        ps = [p for p in apaths if p in changes]
        self.debug("changed paths {}".format(ps))
        changed = bool(ps)
        if ps:
            for p in ps:
                self.debug("adding to index: {}".format(os.path.relpath(p, self.path)))
            self.index.add(ps)

        ps = [p for p in apaths if p in deletes]
        self.debug("delete paths {}".format(ps))
        delete_changed = bool(ps)
        if ps:
            for p in ps:
                self.debug(
                    "removing from index: {}".format(os.path.relpath(p, self.path))
                )
            self.index.remove(ps, working_tree=True)

        return changed or delete_changed

    def add_ignore(self, *args):
        ignores = []
        p = os.path.join(self.path, ".gitignore")
        if os.path.isfile(p):
            with open(p, "r") as rfile:
                ignores = [line.strip() for line in rfile]

        args = [a for a in args if a not in ignores]
        if args:
            with open(p, "a") as afile:
                for a in args:
                    afile.write("{}\n".format(a))
        self.add(p, commit=False)

    def get_modification_date(self, path):
        """
        "Fri May 18 11:13:57 2018 -0600"
        :param path:
        :return:
        """
        d = self.cmd(
            "log",
            "-1",
            '--format="%ad"',
            "--date=format:{}".format(DATE_FORMAT),
            "--",
            path,
        )
        if d:
            d = d[1:-1]
        return d

    def out_of_date(self, branchname=None):
        repo = self._repo
        if branchname is None:
            branchname = repo.active_branch.name

        pd = open_progress(2)

        origin = repo.remotes.origin
        pd.change_message("Fetching {} {}".format(origin, branchname))

        repo.git.fetch(origin, branchname)
        pd.change_message("Complete")
        # try:
        #     oref = origin.refs[branchname]
        #     remote_commit = oref.commit
        # except IndexError:
        #     remote_commit = None
        #
        # branch = getattr(repo.heads, branchname)
        # local_commit = branch.commit
        local_commit, remote_commit = self._get_local_remote_commit(branchname)
        self.debug("out of date {} {}".format(local_commit, remote_commit))
        return local_commit != remote_commit

    def _get_local_remote_commit(self, branchname=None):
        repo = self._repo
        origin = repo.remotes.origin
        try:
            oref = origin.refs[branchname]
            remote_commit = oref.commit
        except IndexError:
            remote_commit = None

        if branchname is None:
            branch = repo.active_branch.name
        else:
            try:
                branch = repo.heads[branchname]
            except AttributeError:
                return None, None

        local_commit = branch.commit
        return local_commit, remote_commit

    @classmethod
    def clone_from(cls, url, path):
        repo = cls()
        if repo.clone(url, path):
            return repo
        # # progress = open_progress(100)
        # #
        # # def func(op_code, cur_count, max_count=None, message=''):
        # #     if max_count:
        # #         progress.max = int(max_count) + 2
        # #         if message:
        # #             message = 'Cloning repository {} -- {}'.format(url, message[2:])
        # #             progress.change_message(message, auto_increment=False)
        # #         progress.update(int(cur_count))
        # #
        # #     if op_code == 66:
        # #         progress.close()
        # # rprogress = CallableRemoteProgress(func)
        # rprogress = None
        # try:
        #     Repo.clone_from(url, path, progress=rprogress)
        # except GitCommandError as e:
        #     print(e)
        #     shutil.rmtree(path)
        #     # def foo():
        #     #     try:
        #     #         Repo.clone_from(url, path, progress=rprogress)
        #     #     except GitCommandError:
        #     #         shutil.rmtree(path)
        #     #
        #     #     evt.set()
        #
        #     # t = Thread(target=foo)
        #     # t.start()
        #     # period = 0.1
        #     # while not evt.is_set():
        #     #     st = time.time()
        #     #     # v = prog.get_value()
        #     #     # if v == n - 2:
        #     #     #     prog.increase_max(50)
        #     #     #     n += 50
        #     #     #
        #     #     # prog.increment()
        #     #     time.sleep(max(0, period - time.time() + st))
        #     # prog.close()

    def clone(self, url, path, reraise=False, **kw):
        # config = 'http.sslVerify={}'.format(globalv.VERIFY_SSL)
        # kw['config'] = config
        try:
            self._repo = Repo.clone_from(url, path, **kw)
            return True
        except GitCommandError as e:
            self.warning_dialog(
                "Cloning error: {}, url={}, path={}".format(e, url, path),
                position=(100, 100),
            )
            if reraise:
                raise

    def unpack_blob(self, hexsha, p):
        """
        p: str. should be absolute path
        """
        repo = self._repo
        tree = repo.commit(hexsha).tree
        # blob = next((bi for ti in tree.trees
        # for bi in ti.blobs
        # if bi.abspath == p), None)
        blob = None
        for ts in ((tree,), tree.trees):
            for ti in ts:
                for bi in ti.blobs:
                    # print bi.abspath, p
                    if bi.abspath == p:
                        blob = bi
                        break
        else:
            print("failed unpacking", p)

        return blob.data_stream.read() if blob else ""

    def shell(self, cmd, *args):
        repo = self._repo

        func = getattr(repo.git, cmd)
        return func(*args)

    def truncate_repo(self, date="1 month"):
        repo = self._repo
        name = os.path.basename(self.path)
        backup = ".{}".format(name)
        repo.git.clone("--mirror", "".format(name), "./{}".format(backup))
        logs = repo.git.log("--pretty=%H", '-after "{}"'.format(date))
        logs = reversed(logs.split("\n"))
        sha = next(logs)

        gpath = os.path.join(self.path, ".git", "info", "grafts")
        with open(gpath, "w") as wfile:
            wfile.write(sha)

        repo.git.filter_branch("--tag-name-filter", "cat", "--", "--all")
        repo.git.gc("--prune=now")

    def get_dag(self, branch=None, delim="$", limit=None, simplify=True):
        fmt_args = ("%H", "%ai", "%ar", "%s", "%an", "%ae", "%d", "%P")
        fmt = delim.join(fmt_args)

        args = [
            "--abbrev-commit",
            "--topo-order",
            "--reverse",
            # '--author-date-order',
            # '--decorate=full',
            "--format={}".format(fmt),
        ]
        if simplify:
            args.append("--simplify-by-decoration")
        if branch == NULL_STR:
            args.append("--all")
        else:
            args.append("-b")
            args.append(branch)
        if limit:
            args.append("-{}".format(limit))

        return self._repo.git.log(*args)

    def commits_iter(self, p, keys=None, limit="-"):
        repo = self._repo
        p = os.path.join(repo.working_tree_dir, p)

        p = p.replace(" ", "\ ")
        hx = repo.git.log(
            "--pretty=%H", "--follow", "-{}".format(limit), "--", p
        ).split("\n")

        def func(hi):
            commit = repo.rev_parse(hi)
            r = [
                hi,
            ]
            if keys:
                r.extend([getattr(commit, ki) for ki in keys])
            return r

        return (func(ci) for ci in hx)

    def odiff(self, a, b, **kw):
        a = self._repo.commit(a)
        return a.diff(b, **kw)

    def diff(self, a, b, *args):
        return self._git_command(lambda g: g.diff(a, b, *args), "diff")

    def status(self):
        return self._git_command(lambda g: g.status(), "status")

    def report_local_changes(self):
        self.debug("Local Changes to {}".format(self.path))
        for p in self.get_local_changes():
            self.debug("\t{}".format(p))

    def commit_dialog(self):
        from pychron.git_archive.commit_dialog import CommitDialog

        ps = self.get_local_changes()
        cd = CommitDialog(ps)
        info = cd.edit_traits()
        if info.result:
            index = self.index
            index.add([mp.path for mp in cd.valid_paths()])
            self.commit(cd.commit_message)
            return True

    def get_local_changes(self, change_type=("M",)):
        repo = self._repo

        diff = repo.index.diff(None)

        return [
            di.a_blob.abspath
            for change_type in change_type
            for di in diff.iter_change_type(change_type)
        ]

        # diff_str = repo.git.diff('HEAD', '--full-index')
        # diff_str = StringIO(diff_str)
        # diff_str.seek(0)
        #
        # class ProcessWrapper:
        #     stderr = None
        #     stdout = None
        #
        #     def __init__(self, f):
        #         self._f = f
        #
        #     def wait(self, *args, **kw):
        #         pass
        #
        #     def read(self):
        #         return self._f.read()
        #
        # proc = ProcessWrapper(diff_str)
        #
        # diff = Diff._index_from_patch_format(repo, proc)
        # root = self.path
        #
        #
        #
        # for diff_added in hcommit.diff('HEAD~1').iter_change_type('A'):
        #     print(diff_added)

        # diff = hcommit.diff()
        # diff = repo.index.diff(repo.head.commit)
        # return [os.path.relpath(di.a_blob.abspath, root) for di in diff.iter_change_type('M')]

        # patches = map(str.strip, diff_str.split('diff --git'))
        # patches = ['\n'.join(p.split('\n')[2:]) for p in patches[1:]]
        #
        # diff_str = StringIO(diff_str)
        # diff_str.seek(0)
        # index = Diff._index_from_patch_format(repo, diff_str)
        #
        # return index, patches
        #

    def get_head(self, commit=True, hexsha=True):
        head = self._repo
        if commit:
            head = head.commit()

        if hexsha:
            head = head.hexsha
        return head
        # return self._repo.head.commit.hexsha

    def cmd(self, cmd, *args):
        return getattr(self._repo.git, cmd)(*args)

    def is_dirty(self):
        return self._repo.is_dirty()

    def untracked_files(self):
        lines = self._repo.git.status(porcelain=True, untracked_files=True)
        # Untracked files preffix in porcelain mode
        prefix = "?? "
        untracked_files = list()
        iswindows = sys.platform == "win32"
        for line in lines.split("\n"):
            if not line.startswith(prefix):
                continue
            filename = line[len(prefix) :].rstrip("\n")
            # Special characters are escaped
            if filename[0] == filename[-1] == '"':
                filename = filename[1:-1].decode("string_escape")

            if iswindows:
                filename = filename.replace("/", "\\")

            untracked_files.append(os.path.join(self.path, filename))
        # finalize_process(proc)
        return untracked_files

    def has_staged(self):
        return self._repo.git.diff("HEAD", "--name-only")
        # return self._repo.is_dirty()

    def has_unpushed_commits(self, remote="origin", branch="master"):
        if self._repo:
            branch = self._clean_master_branch(branch)
            # return self._repo.git.log('--not', '--remotes', '--oneline')
            if remote in self._repo.remotes:
                return self._repo.git.log(
                    "{}/{}..HEAD".format(remote, branch), "--oneline"
                )

    def add_unstaged(self, root=None, add_all=False, extension=None, use_diff=False):
        if root is None:
            root = self.path

        index = self.index

        def func(ps, extension):
            if extension:
                if not isinstance(extension, tuple):
                    extension = (extension,)
                ps = [pp for pp in ps if os.path.splitext(pp)[1] in extension]

            if ps:
                self.debug("adding to index {}".format(ps))

                index.add(ps)

        if use_diff:
            pass
            # try:
            # ps = [diff.a_blob.path for diff in index.diff(None)]
            # func(ps, extension)
            # except IOError,e:
            # print 'exception', e
        elif add_all:
            self._repo.git.add(".")
        else:
            for r, ds, fs in os.walk(root):
                ds[:] = [d for d in ds if d[0] != "."]
                ps = [os.path.join(r, fi) for fi in fs]
                func(ps, extension)

    def update_gitignore(self, *args):
        p = os.path.join(self.path, ".gitignore")
        # mode = 'a' if os.path.isfile(p) else 'w'
        args = list(args)
        if os.path.isfile(p):
            with open(p, "r") as rfile:
                for line in fileiter(rfile, strip=True):
                    for i, ai in enumerate(args):
                        if line == ai:
                            args.pop(i)
        if args:
            with open(p, "a") as wfile:
                for ai in args:
                    wfile.write("{}\n".format(ai))
            self._add_to_repo(p, msg="updated .gitignore")

    def get_commit(self, hexsha):
        repo = self._repo
        return repo.commit(hexsha)

    def tag_branch(self, tagname):
        repo = self._repo
        repo.create_tag(tagname)

    def get_current_branch(self):
        repo = self._repo
        return repo.active_branch.name

    def restore_branch(self, ps):
        self._repo.git.restore("--staged", ps)
        self._repo.git.restore(ps)

    def checkout(self, *args, **kw):
        self._repo.git.checkout(*args, **kw)

    def reset(self):
        """delete index.lock"""
        p = os.path.join(self._repo.working_dir, ".git", "index.lock")
        if os.path.isfile(p):
            os.remove(p)

    def checkout_branch(self, name, inform=True, load_history=True):
        repo = self._repo
        if name.startswith("origin"):
            self.warning_dialog("Contact developer")
            # name = name[7:]
            # remote = repo.remote()
            # rref = getattr(remote.refs, name)
            # repo.create_head(name, rref)
            #
            # branch = repo.heads[name]
            # branch.set_tracking_branch(rref)

        else:
            branch = getattr(repo.heads, name)

        try:
            branch.checkout()
            self.selected_branch = name
            if load_history:
                self._load_branch_history()
            if inform:
                self.information_dialog('Repository now on branch "{}"'.format(name))

        except BaseException as e:
            self.debug_exception()
            self.warning_dialog(
                'There was an issue trying to checkout branch "{}"'.format(name)
            )
            raise e

    def delete_branch(self, name):
        self._repo.delete_head(name)

    def get_branch(self, name):
        return getattr(self._repo.heads, name)

    def create_branch(self, name=None, commit="HEAD", inform=True, push=False):
        repo = self._repo

        if name is None:
            nb = NewBranchView(branches=repo.branches)
            info = nb.edit_traits()
            if info.result:
                name = nb.name
            else:
                return

        if name not in repo.branches:
            branch = repo.create_head(name, commit=commit)
            branch.checkout()

            if push and repo.remotes:
                origin = repo.remotes.origin
                repo.git.push("--set-upstream", origin, repo.head.ref)
            if inform:
                self.information_dialog('Repository now on branch "{}"'.format(name))
            return name

    def create_remote(self, url, name="origin", force=False):
        repo = self._repo
        if repo:
            self.debug("setting remote {} {}".format(name, url))
            # only create remote if doesnt exist
            if not hasattr(repo.remotes, name):
                self.debug("create remote {}".format(name, url))
                repo.create_remote(name, url)
            elif force:
                repo.delete_remote(name)
                repo.create_remote(name, url)

    def delete_remote(self, name="origin"):
        repo = self._repo
        if repo:
            if hasattr(repo.remotes, name):
                repo.delete_remote(name)

    def get_branch_names(self):
        return [b.name for b in self._repo.branches] + [
            b.name for b in self._repo.remote().refs if b.name.lower() != "origin/head"
        ]

    def git_history_view(self, branchname):
        repo = self._repo
        h = BaseGitHistory(branchname=branchname)

        origin = repo.remotes.origin
        try:
            oref = origin.refs[branchname]
            remote_commit = oref.commit
        except IndexError:
            remote_commit = None

        branch = self.get_branch(branchname)
        local_commit = branch.commit
        h.local_commit = str(local_commit)

        txt = repo.git.rev_list(
            "--left-right", "{}...{}".format(local_commit, remote_commit)
        )
        commits = [ci[1:] for ci in txt.split("\n")]

        commits = [repo.commit(i) for i in commits]
        h.set_items(commits)
        commit_view = CommitView(model=h)
        return commit_view

    def _clean_master_branch(self, branch):
        for ref in self._repo.references:
            if ref.name == branch:
                ret = branch
                break
        else:
            ret = branch
            if branch == "master":
                ret = "main"

        self.debug("clean master in = {} out={}".format(branch, ret))
        return ret

    def pull(
        self,
        branch="master",
        remote="origin",
        handled=True,
        use_progress=True,
        use_auto_pull=False,
    ):
        """
        fetch and merge

        if use_auto_pull is False ask user if they want to accept the available updates
        """

        self.debug("pulling {} from {}".format(branch, remote))

        repo = self._repo
        try:
            remote = self._get_remote(remote)
        except AttributeError as e:
            print("repo man pull", e)
            return

        if remote:
            self.debug("pulling from url: {}".format(remote.url))

            branch = self._clean_master_branch(branch)
            if use_progress:
                prog = open_progress(
                    3,
                    show_percent=False,
                    title="Pull Repository {}".format(self.name),
                    close_at_end=False,
                )
                prog.change_message(
                    'Fetching branch:"{}" from "{}"'.format(branch, remote)
                )
            try:
                self.fetch(remote)
            except GitCommandError as e:
                self.debug(e)
                if not handled:
                    raise e
            self.debug("fetch complete")

            def merge():
                try:
                    repo.git.merge("FETCH_HEAD")
                except GitCommandError as e:
                    self.critical("Pull-merge FETCH_HEAD={}".format(e))
                    self.smart_pull(branch=branch, remote=remote)

            if not use_auto_pull:
                ahead, behind = self.ahead_behind(remote)
                if behind:
                    if self.confirmation_dialog(
                        'Repository "{}" is behind the official version by {} changes.\n'
                        "Would you like to pull the available changes?".format(
                            self.name, behind
                        )
                    ):
                        # show the changes
                        h = self.git_history_view(branch)
                        info = h.edit_traits(kind="livemodal")
                        if info.result:
                            merge()
            else:
                merge()

            if use_progress:
                prog.close()

        self.debug("pull complete")

    def has_remote(self, remote="origin"):
        return bool(self._get_remote(remote))

    def push(self, branch=None, remote=None, inform=False):
        if remote is None:
            remote = "origin"

        rr = self._get_remote(remote)
        if rr:
            if branch is None:
                branch = self._repo.active_branch.name
            try:
                self._repo.git.push(remote, branch)
                if inform:
                    self.information_dialog("{} push complete".format(self.name))
            except GitCommandError as e:
                if branch == "master":
                    self.debug("retrying push")
                    try:
                        self._repo.git.push(remote, "main")
                        if inform:
                            self.information_dialog(
                                "{} push complete".format(self.name)
                            )
                    except GitCommandError as e:
                        self.debug_exception()
                else:
                    self.debug_exception()

                if inform:
                    self.warning_dialog(
                        "{} push failed. See log file for more details".format(
                            self.name
                        )
                    )
            # self._git_command(lambda g: g.push(remote, branch), tag='GitRepoManager.push')
        else:
            self.warning('No remote called "{}"'.format(remote))

    def _git_command(self, func, tag):
        try:
            return func(self._repo.git)
        except GitCommandError as e:
            self.warning("Git command failed. {}, {}".format(e, tag))

    def rebase(self, onto_branch="master"):
        if self._repo:
            repo = self._repo
            branch = self.get_current_branch()
            if onto_branch.startswith("origin"):
                remote = repo.remotes.origin
                try:
                    bn = onto_branch[7:]
                    onto_branch = getattr(remote.refs, bn)
                except AttributeError:
                    onto_branch = None
            else:
                self.checkout_branch(onto_branch)
                self.pull()

            if onto_branch is not None:
                repo.git.rebase(onto_branch, branch)

    def smart_pull(
        self,
        branch="master",
        remote="origin",
        quiet=True,
        accept_our=False,
        accept_their=False,
    ):
        if remote not in self._repo.remotes:
            return True

        try:
            ahead, behind = self.ahead_behind(remote)
        except GitCommandError as e:
            self.debug("Smart pull error: {}".format(e))
            return

        self.debug("Smart pull ahead: {} behind: {}".format(ahead, behind))
        repo = self._repo
        if behind:
            if ahead:
                if not quiet:
                    if not self.confirmation_dialog(
                        "You are {} behind and {} commits ahead. "
                        "There are potential conflicts that you will have to resolve."
                        "\n\nWould you like to Continue?".format(behind, ahead)
                    ):
                        return

                # check for unresolved conflicts
                # self._resolve_conflicts(branch, remote, accept_our, accept_their, True)
                try:
                    repo.git.merge("--abort")
                except GitCommandError:
                    pass

                # potentially conflicts
                with StashCTX(repo) as error:
                    if error:
                        self.warning_dialog(
                            "Failed stashing your local changes. "
                            "Fix repository {} "
                            "before proceeding. {}".format(
                                os.path.basename(repo.working_dir), error
                            )
                        )

                        return

                    branch = self._clean_master_branch(branch)

                    # do merge
                    try:
                        # repo.git.rebase('--preserve-merges', '{}/{}'.format(remote, branch))
                        repo.git.merge("{}/{}".format(remote, branch))
                    except GitCommandError:
                        if self.confirmation_dialog(
                            "There appears to be a conflict with {}."
                            "\n\nWould you like to accept the master copy (Yes).\n\nOtherwise "
                            "you will need to merge the changes manually (No)".format(
                                self.name
                            )
                        ):
                            try:
                                repo.git.merge("--abort")
                            except GitCommandError:
                                pass

                            try:
                                repo.git.reset("--hard", "{}/{}".format(remote, branch))
                            except GitCommandError:
                                pass
                        elif self.confirmation_dialog(
                            "Would you like to accept all of your current changes even "
                            "though there are newer changes available?"
                        ):
                            accept_our = True
                #                             try:
                #                                 repo.git.pull('-X', 'theirs', '--commit', '--no-edit')
                #                                 return True
                #                             except GitCommandError:
                #                                 clean = repo.git.clean('-n')
                #                                 if clean:
                #                                     if self.confirmation_dialog('''You have untracked files that could be an issue.
                # {}
                #
                # You like to delete them and try again?'''.format(clean)):
                #                                         try:
                #                                             repo.git.clean('-fd')
                #                                         except GitCommandError:
                #                                             self.warning_dialog('Failed to clean repository')
                #                                             return
                #
                #                                         try:
                #                                             repo.git.pull('-X', 'theirs', '--commit', '--no-edit')
                #                                             return True
                #                                         except GitCommandError:
                #                                             self.warning_dialog('Failed pulling changes for {}'.format(self.name))
                #                                 else:
                #                                     self.warning_dialog('Failed pulling changes for {}'.format(self.name))
                #                                 return

                self._resolve_conflicts(branch, remote, accept_our, accept_their, quiet)
            else:
                self.debug("merging {} commits".format(behind))
                self._git_command(
                    lambda g: g.merge("-X", "theirs", "FETCH_HEAD"),
                    "GitRepoManager.smart_pull/!ahead",
                )
        else:
            self.debug("Up-to-date with {}".format(remote))
            if not quiet:
                self.information_dialog(
                    'Repository "{}" up-to-date with {}'.format(self.name, remote)
                )

        return True

    def fetch(self, remote="origin"):
        if self._repo:
            return self._git_command(lambda g: g.fetch(remote), "GitRepoManager.fetch")
            # return self._repo.git.fetch(remote)

    def ahead_behind(self, remote="origin"):
        self.debug("ahead behind")

        repo = self._repo
        ahead, behind = ahead_behind(repo, remote)

        return ahead, behind

    def merge(self, from_, to_=None, inform=True):
        repo = self._repo

        if to_:
            dest = getattr(repo.branches, to_)
            dest.checkout()

        if from_.startswith("origin"):
            remote = repo.remotes.origin
            try:
                bn = from_[7:]
                from_ = getattr(remote.refs, bn)
            except AttributeError:
                self.debug("available branches {}".format(repo.branches))
                msg = "Could not locate {} for merge".format(from_)
                self.warning(msg)
                if inform:
                    self.warning_dialog(msg)

                return
        else:
            from_ = getattr(repo.branches, from_)

        with StashCTX(repo):
            try:
                repo.git.merge(from_)
            except GitCommandError:
                self.debug_exception()
                if inform:
                    self.warning_dialog(
                        "Merging {} into {} failed. See log file for more details".format(
                            from_, to_
                        )
                    )

    def commit(self, msg, author=None):
        self.debug("commit message={}, author={}".format(msg, author))

        index = self.index
        if index:
            try:
                index.commit(msg, author=author, committer=author)
                return True
            except git.exc.GitError as e:
                self.warning("Commit failed: {}".format(e))

    def add(self, p, msg=None, msg_prefix=None, verbose=True, **kw):
        repo = self._repo
        # try:
        #     n = len(repo.untracked_files)
        # except IOError:
        #     n = 0

        # try:
        #     if not repo.is_dirty() and not n:
        #         return
        # except OSError:
        #     pass

        bp = os.path.basename(p)
        dest = os.path.join(repo.working_dir, p)

        dest_exists = os.path.isfile(dest)
        if msg_prefix is None:
            msg_prefix = "modified" if dest_exists else "added"

        if not dest_exists:
            self.debug("copying to destination.{}>>{}".format(p, dest))
            shutil.copyfile(p, dest)

        if msg is None:
            msg = "{}".format(bp)
        msg = "{} - {}".format(msg_prefix, msg)
        if verbose:
            self.debug("add to repo msg={}".format(msg))

        self._add_to_repo(dest, msg, **kw)

    def get_log(self, branch, *args):
        if branch is None:
            branch = self._repo.active_branch

        # repo = self._repo
        # l = repo.active_branch.log(*args)
        return self.cmd("log", branch, "--oneline", *args).split("\n")

    def get_commits_from_log(
        self, greps=None, max_count=None, after=None, before=None, path=None
    ):
        repo = self._repo
        args = [repo.active_branch.name, "--remove-empty", "--simplify-merges"]
        if max_count:
            args.append("--max-count={}".format(max_count))
        if after:
            args.append("--after={}".format(after))
        if before:
            args.append("--before={}".format(before))

        if greps:
            greps = "\|".join(greps)
            args.append("--grep=^{}".format(greps))

        args.append(LOGFMT)
        if path:
            args.append("--")
            args.append(path)
        # txt = self.cmd('log', *args)
        # self.debug('git log {}'.format(' '.join(args)))

        cs = self._gitlog_commits(args)
        return cs

    def get_active_branch(self):
        return self._repo.active_branch.name

    def get_sha(self, path=None):
        sha = ""
        if path:
            logstr = self.cmd("ls-tree", "HEAD", path)
            try:
                mode, kind, sha_name = logstr.split(" ")
                sha, name = sha_name.split("\t")
            except ValueError:
                pass

        return sha

    def get_branch_diff(self, from_, to_):
        args = ("{}..{}".format(from_, to_), LOGFMT)
        return self._gitlog_commits(args)

    def add_tag(self, name, message, hexsha=None):
        args = ("-a", name, "-m", message)
        if hexsha:
            args = args + (hexsha,)

        self.cmd("tag", *args)

    # action handlers
    def diff_selected(self):
        if self._validate_diff():
            if len(self.selected_commits) == 2:
                l, r = self.selected_commits
                dv = self._diff_view_factory(l, r)
                open_view(dv)

    def revert_to_selected(self):
        # check for uncommitted changes
        # warn user the uncommitted changes will be lost if revert now

        commit = self.selected_commits[-1]
        self.revert(commit.hexsha, self.selected)

    def revert(self, hexsha, path):
        self._repo.git.checkout(hexsha, path)
        self.path_dirty = path
        self._set_active_commit()

    def revert_commit(self, hexsha):
        self._git_command(lambda g: g.revert(hexsha), "revert_commit")

    def load_file_history(self, p):
        repo = self._repo
        try:
            hexshas = repo.git.log("--pretty=%H", "--follow", "--", p).split("\n")

            self.selected_path_commits = self._parse_commits(hexshas, p)
            self._set_active_commit()

        except GitCommandError:
            self.selected_path_commits = []

    def get_modified_files(self, hexsha):
        def func(git):
            return git.diff_tree("--no-commit-id", "--name-only", "-r", hexsha)

        txt = self._git_command(func, "get_modified_files")
        return txt.split("\n")

    # private
    def _gitlog_commits(self, args):
        txt = self._git_command(lambda g: g.log(*args), "log")

        cs = []
        if txt:
            cs = [from_gitlog(l.strip()) for l in txt.split("\n")]
        return cs

    def _resolve_conflicts(self, branch, remote, accept_our, accept_their, quiet):
        conflict_paths = self._get_conflict_paths()
        self.debug("resolve conflict_paths: {}".format(conflict_paths))
        if conflict_paths:
            mm = MergeModel(conflict_paths, branch=branch, remote=remote, repo=self)
            if accept_our:
                mm.accept_our()
            elif accept_their:
                mm.accept_their()
            else:
                mv = MergeView(model=mm)
                mv.edit_traits(kind="livemodal")
        else:
            if not quiet:
                self.information_dialog("There were no conflicts identified")

    def _get_conflict_paths(self):
        def func(git):
            return git.diff("--name-only", "--diff-filter=U")

        txt = self._git_command(func, "get conflict paths")
        return [line for line in txt.split("\n") if line.strip()]

    def _validate_diff(self):
        return True

    def _diff_view_factory(self, a, b):
        # d = self.diff(a.hexsha, b.hexsha)
        if not a.blob:
            a.blob = self.unpack_blob(a.hexsha, a.name)

        if not b.blob:
            b.blob = self.unpack_blob(b.hexsha, b.name)

        model = DiffModel(left_text=b.blob, right_text=a.blob)
        dv = DiffView(model=model)
        return dv

    def _add_to_repo(self, p, msg, commit=True):
        index = self.index
        if index:
            if not isinstance(p, list):
                p = [p]
            try:
                index.add(p)
            except IOError as e:
                self.warning('Failed to add file. Error:"{}"'.format(e))

                # an IOError has been caused in the past by "'...index.lock' could not be obtained"
                os.remove(os.path.join(self.path, ".git", "index.lock"))
                try:
                    self.warning('Retry after "Failed to add file"'.format(e))
                    index.add(p)
                except IOError as e:
                    self.warning('Retry failed. Error:"{}"'.format(e))
                    return

            if commit:
                index.commit(msg)

    def _get_remote(self, remote):
        repo = self._repo
        try:
            return getattr(repo.remotes, remote)
        except AttributeError:
            pass

    def _get_branch_history(self):
        repo = self._repo
        hexshas = repo.git.log("--pretty=%H").split("\n")
        return hexshas

    def _load_branch_history(self):
        hexshas = self._get_branch_history()
        self.commits = self._parse_commits(hexshas)

    def _parse_commits(self, hexshas, p=""):
        def factory(ci):
            repo = self._repo
            obj = repo.rev_parse(ci)
            cx = GitSha(
                message=obj.message,
                hexsha=obj.hexsha,
                name=p,
                date=obj.committed_datetime,
            )
            # date=format_date(obj.committed_date))
            return cx

        return [factory(ci) for ci in hexshas]

    def _set_active_commit(self):
        p = self.selected
        with open(p, "r") as rfile:
            chexsha = hashlib.sha1(rfile.read()).hexdigest()

        for c in self.selected_path_commits:
            blob = self.unpack_blob(c.hexsha, p)
            c.active = chexsha == hashlib.sha1(blob).hexdigest() if blob else False

        self.refresh_commits_table_needed = True

    # handlers
    def _selected_fired(self, new):
        if new:
            self._selected_hook(new)
            self.load_file_history(new)

    def _selected_hook(self, new):
        pass

    def _remote_changed(self, new):
        if new:
            self.delete_remote()
            r = "https://github.com/{}".format(new)
            self.create_remote(r)

    @property
    def index(self):
        return self._repo.index

    @property
    def active_repo(self):
        return self._repo


if __name__ == "__main__":
    repo = GitRepoManager()
    repo.open_repo("/Users/ross/Sandbox/mergetest/blocal")
    repo.smart_pull()

    # rp = GitRepoManager()
    # rp.init_repo('/Users/ross/Pychrondata_dev/scripts')
    # rp.commit_dialog()

    # ============= EOF =============================================
    # repo manager protocol
    # def get_local_changes(self, repo=None):
    # repo = self._get_repo(repo)
    #     diff_str = repo.git.diff('--full-index')
    #     patches = map(str.strip, diff_str.split('diff --git'))
    #     patches = ['\n'.join(p.split('\n')[2:]) for p in patches[1:]]
    #
    #     diff_str = StringIO(diff_str)
    #     diff_str.seek(0)
    #     index = Diff._index_from_patch_format(repo, diff_str)
    #
    #     return index, patches
    # def is_dirty(self, repo=None):
    #     repo = self._get_repo(repo)
    #     return repo.is_dirty()
    # def get_untracked(self):
    #     return self._repo.untracked_files
    #     def _add_repo(self, root):
    # existed=True
    # if not os.path.isdir(root):
    #     os.mkdir(root)
    #     existed=False
    #
    # gitdir=os.path.join(root, '.git')
    # if not os.path.isdir(gitdir):
    #     repo = Repo.init(root)
    #     existed = False
    # else:
    #     repo = Repo(root)
    #
    # return repo, existed

    # def add_repo(self, localpath):
    #     """
    #         add a blank repo at ``localpath``
    #     """
    #     repo, existed=self._add_repo(localpath)
    #     self._repo=repo
    #     self.root=localpath
    #     return existed
