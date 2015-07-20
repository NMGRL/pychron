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

from traits.api import Any, Str, List, Event
# ============= standard library imports ========================
import hashlib
from datetime import datetime
import os
import shutil
from cStringIO import StringIO
import time
from git.exc import GitCommandError
from git import Repo, Diff
# ============= local library imports  ==========================
from pychron.core.codetools.inspection import caller
from pychron.core.helpers.filetools import fileiter
from pychron.core.progress import open_progress
from pychron.envisage.view_util import open_view
from pychron.git_archive.diff_view import DiffView, DiffModel
from pychron.git_archive.views import NewBranchView
from pychron.loggable import Loggable
from pychron.git_archive.commit import Commit


def format_date(d):
    return time.strftime("%m/%d/%Y %H:%M", time.gmtime(d))


def isoformat_date(d):
    if isinstance(d, (float, int)):
        d = datetime.fromtimestamp(d)

    return d.strftime('%Y-%m-%d %H:%M:%S')
    # return time.mktime(time.gmtime(d))


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

        self.logger = None
        self.name = '{}<GitRepo>'.format(os.path.basename(p))

        if os.path.isdir(p):
            self.init_repo(p)
            return True
        else:
            os.mkdir(p)
            repo = Repo.init(p)
            self.debug('created new repo {}'.format(p))
            self._repo = repo
            return False

    def init_repo(self, path):
        """
            path: absolute path to repo

            return True if git repo exists
        """
        if os.path.isdir(path):
            g = os.path.join(path, '.git')
            if os.path.isdir(g):
                self._repo = Repo(path)
                return True
            else:
                self.debug('{} is not a valid repo. Initializing now'.format(path))
                self._repo = Repo.init(path)

    def add_paths(self, apaths):
        if not hasattr(apaths, '__iter__'):
            apaths = (apaths,)

        changes = self.get_local_changes()
        if not changes:
            changes = self.untracked_files()
        else:
            changes = [os.path.join(self.path, c) for c in changes]

        ps = [p for p in apaths if p in changes]
        changed = bool(ps)
        for p in ps:
            self.debug('adding to index: {}'.format(os.path.relpath(p, self.path)))
        self.index.add(ps)
        return changed

    def add_ignore(self, *args):
        ignores = []
        p = os.path.join(self.path, '.gitignore')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                ignores = [line.strip() for line in rfile]

        args = [a for a in args if a not in ignores]
        if args:
            with open(p, 'a') as afile:
                for a in args:
                    afile.write('{}\n'.format(a))
        self.add(p, commit=False)

    def out_of_date(self, branchname='master'):
        pd = open_progress(2)

        repo = self._repo
        origin = repo.remotes.origin
        pd.change_message('Fetching {} {}'.format(origin, branchname))
        repo.git.fetch(origin, branchname)
        pd.change_message('Complete')
        # try:
        #     oref = origin.refs[branchname]
        #     remote_commit = oref.commit
        # except IndexError:
        #     remote_commit = None
        #
        # branch = getattr(repo.heads, branchname)
        # local_commit = branch.commit
        local_commit, remote_commit = self._get_local_remote_commit(branchname)
        self.debug('out of date {} {}'.format(local_commit, remote_commit))
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
            branch = repo.head
        else:
            try:
                branch = repo.heads[branchname]
            except AttributeError:
                return None, None

        local_commit = branch.commit
        return local_commit, remote_commit

    def clone(self, url, path):
        self._repo = Repo.clone_from(url, path)

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
            print 'failed unpacking', p

        return blob.data_stream.read() if blob else ''

    def shell(self, cmd, *args):
        repo = self._repo

        func = getattr(repo.git, cmd)
        return func(*args)

    def truncate_repo(self, date='1 month'):
        repo = self._repo
        name = os.path.basename(self.path)
        backup = '.{}'.format(name)
        repo.git.clone('--mirror', ''.format(name), './{}'.format(backup))
        logs = repo.git.log('--pretty=%H', '-after "{}"'.format(date))
        logs = reversed(logs.split('\n'))
        sha = logs.next()

        gpath = os.path.join(self.path, '.git', 'info', 'grafts')
        with open(gpath, 'w') as wfile:
            wfile.write(sha)

        repo.git.filter_branch('--tag-name-filter', 'cat', '--', '--all')
        repo.git.gc('--prune=now')

    def commits_iter(self, p, keys=None, limit='-'):
        repo = self._repo
        p = os.path.join(repo.working_tree_dir, p)

        p = p.replace(' ', '\ ')
        hx = repo.git.log('--pretty=%H', '--follow', '-{}'.format(limit), '--', p).split('\n')

        def func(hi):
            commit = repo.rev_parse(hi)
            r = [hi, ]
            if keys:
                r.extend([getattr(commit, ki) for ki in keys])
            return r

        return (func(ci) for ci in hx)

    def diff(self, a, b):
        repo = self._repo
        return repo.git.diff(a, b, )

    def report_status(self):
        self.debug('Local Changes to {}'.format(self.path))
        for p in self.get_local_changes():
            self.debug('\t{}'.format(p))

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

    def get_local_changes(self):
        repo = self._repo
        diff_str = repo.git.diff('HEAD', '--full-index')
        diff_str = StringIO(diff_str)
        diff_str.seek(0)
        diff = Diff._index_from_patch_format(repo, diff_str)
        root = self.path
        return [os.path.relpath(di.a_blob.abspath, root) for di in diff.iter_change_type('M')]

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
        lines = self._repo.git.status(porcelain=True,
                                      untracked_files=True)

        # Untracked files preffix in porcelain mode
        prefix = "?? "
        untracked_files = list()
        for line in lines.split('\n'):
            # print 'ffff', line
            if not line.startswith(prefix):
                continue
            filename = line[len(prefix):].rstrip('\n')
            # Special characters are escaped
            if filename[0] == filename[-1] == '"':
                filename = filename[1:-1].decode('string_escape')
            # print 'ffasdfsdf', filename
            untracked_files.append(os.path.join(self.path, filename))
        # finalize_process(proc)
        return untracked_files

    def has_staged(self):
        return self._repo.git.diff('HEAD', '--name-only')
        # return self._repo.is_dirty()

    def has_unpushed_commits(self, remote='origin', branch='master'):
        # return self._repo.git.log('--not', '--remotes', '--oneline')
        return self._repo.git.log('{}/{}..HEAD'.format(remote, branch), '--oneline')

    def add_unstaged(self, root, extension=None, use_diff=False):
        index = self.index

        def func(ps, extension):
            if extension:
                if not isinstance(extension, tuple):
                    extension = (extension,)
                ps = [pp for pp in ps if os.path.splitext(pp)[1] in extension]

            if ps:
                self.debug('adding to index {}'.format(ps))
                index.add(ps)

        if use_diff:
            pass
            # try:
            # ps = [diff.a_blob.path for diff in index.diff(None)]
            # func(ps, extension)
            # except IOError,e:
            # print 'exception', e
        else:
            for r, ds, fs in os.walk(root):
                ps = [os.path.join(r, fi) for fi in fs]
                func(ps, extension)

    def update_gitignore(self, *args):
        p = os.path.join(self.path, '.gitignore')
        # mode = 'a' if os.path.isfile(p) else 'w'
        args = list(args)
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                for line in fileiter(rfile, strip=True):
                    for i, ai in enumerate(args):
                        if line == ai:
                            args.pop(i)
        if args:
            with open(p, 'a') as wfile:
                for ai in args:
                    wfile.write('{}\n'.format(ai))
            self._add_to_repo(p, msg='updated .gitignore')

    def get_commit(self, hexsha):
        repo = self._repo
        return repo.commit(hexsha)

    def tag_branch(self, tagname):
        repo = self._repo
        repo.create_tag(tagname)

    def get_current_branch(self):
        repo = self._repo
        return repo.active_branch.name

    def checkout_branch(self, name):
        repo = self._repo
        branch = getattr(repo.heads, name)
        branch.checkout()

        self.selected_branch = name
        self._load_branch_history()

    def create_branch(self, name=None, commit='HEAD'):
        if name is None:
            nb = NewBranchView()
            info = nb.edit_traits()
            if info.result:
                name = nb.name
            else:
                return

        repo = self._repo
        if name not in repo.branches:
            branch = repo.create_head(name, commit=commit)
            branch.checkout()
            self.information_dialog('Data set not on branch "{}"'.format(name))
        else:
            self.information_dialog('Branch "{}" already exists. Choose a different name'.format(name))
            # branch.commit = repo.head.commit
            # self.checkout_branch(name)

    def create_remote(self, url, name='origin', force=False):
        repo = self._repo
        if repo:
            self.debug('setting remote {} {}'.format(name, url))
            # only create remote if doesnt exist
            if not hasattr(repo.remotes, name):
                self.debug('create remote {}'.format(name, url))
                repo.create_remote(name, url)
            elif force:
                repo.delete_remote(name)
                repo.create_remote(name, url)

    def delete_remote(self, name='origin'):
        repo = self._repo
        if repo:
            if hasattr(repo.remotes, name):
                repo.delete_remote(name)

    def get_branch_names(self):
        return [b.name for b in self._repo.branches]

    @caller
    def pull(self, branch='master', remote='origin', handled=True, use_progress=True):
        """
            fetch and merge
        """
        repo = self._repo
        try:
            remote = self._get_remote(remote)
        except AttributeError, e:
            print 'repo man pull', e
            return

        if remote:
            if use_progress:
                prog = open_progress(3)
                prog.change_message('Fetching {}, branch={}'.format(remote, branch))
            try:
                repo.git.fetch(remote)
            except GitCommandError, e:
                self.debug(e)
                if not handled:
                    raise e

            if use_progress:
                prog.change_message('Merging')

            try:
                repo.git.merge('FETCH_HEAD')
            except GitCommandError, e:
                self.debug(e)
                if not handled:
                    raise e

            if use_progress:
                prog.close()

    def has_remote(self, remote='origin'):
        return bool(self._get_remote(remote))

    def push(self, branch='master', remote='origin'):
        repo = self._repo
        rr = self._get_remote(remote)
        if rr:
            repo.git.push(remote, branch)
        else:
            self.warning('No remote called "{}"'.format(remote))

    def merge(self, src, dest):
        repo = self._repo
        dest = getattr(repo.branches, dest)
        dest.checkout()

        src = getattr(repo.branches, src)
        repo.git.merge(src.commit)

    def commit(self, msg):
        index = self.index
        if index:
            index.commit(msg)

    def add(self, p, msg=None, msg_prefix=None, verbose=True, **kw):
        repo = self._repo
        if not repo.is_dirty():
            return

        bp = os.path.basename(p)
        dest = os.path.join(repo.working_dir, p)

        dest_exists = os.path.isfile(dest)
        if msg_prefix is None:
            msg_prefix = 'modified' if dest_exists else 'added'

        if not dest_exists:
            shutil.copyfile(p, dest)

        if msg is None:
            msg = '{}'.format(bp)
        msg = '{} - {}'.format(msg_prefix, msg)
        if verbose:
            self.debug('add to repo msg={}'.format(msg))

        self._add_to_repo(dest, msg, **kw)

    def get_log(self, branch, *args):
        if branch is None:
            branch = self._repo.active_branch

        # repo = self._repo
        # l = repo.active_branch.log(*args)
        l = self.cmd('log', branch, '--oneline', *args)
        return l.split('\n')

    def get_active_branch(self):
        return self._repo.active_branch.name

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

    def load_file_history(self, p):
        repo = self._repo
        try:
            hexshas = repo.git.log('--pretty=%H', '--follow', '--', p).split('\n')

            self.selected_path_commits = self._parse_commits(hexshas, p)
            self._set_active_commit()

        except GitCommandError:
            self.selected_path_commits = []

    # private
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

            index.add(p)
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
        hexshas = repo.git.log('--pretty=%H').split('\n')
        return hexshas

    def _load_branch_history(self):
        hexshas = self._get_branch_history()
        self.commits = self._parse_commits(hexshas)

    def _parse_commits(self, hexshas, p=''):
        def factory(ci):
            repo = self._repo
            obj = repo.rev_parse(ci)
            cx = Commit(message=obj.message,
                        hexsha=obj.hexsha,
                        name=p,
                        date=format_date(obj.committed_date))
            return cx

        return [factory(ci) for ci in hexshas]

    def _set_active_commit(self):
        p = self.selected
        with open(p, 'r') as rfile:
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
            r = 'https://github.com/{}'.format(new)
            self.create_remote(r)

    @property
    def index(self):
        return self._repo.index

    @property
    def active_repo(self):
        return self._repo

if __name__ == '__main__':
    rp = GitRepoManager()
    rp.init_repo('/Users/ross/Pychrondata_dev/scripts')
    rp.commit_dialog()

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
