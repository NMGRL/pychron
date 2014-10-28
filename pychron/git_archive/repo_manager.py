# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
import shutil
from cStringIO import StringIO
import time

from traits.api import Any, Str, List



#============= standard library imports ========================
import os
from git.exc import GitCommandError
from git import Repo, Diff
# from dulwich.repo import Repo
#============= local library imports  ==========================
from pychron.core.helpers.filetools import fileiter
from pychron.loggable import Loggable
from pychron.git_archive.commit import Commit


class GitRepoManager(Loggable):
    """
        manage a local git repository

    """

    _repo = Any
    # root=Directory
    path = Str
    selected = Any
    selected_branch =Str
    selected_path_commits = List
    selected_commit = List

    def open_repo(self, name, root=None):
        """
            name: name of repo
            root: root directory to create new repo
            index: path to sqlite index

            create master and working branches
        """
        if root is None:
            p = name
        else:
            p = os.path.join(root, name)

        self.path = p

        if os.path.isdir(p):
            self.init_repo(p)
        else:
            os.mkdir(p)
            repo = Repo.init(p)
            self.debug('created new repo {}'.format(p))
            self._repo = repo

    def init_repo(self, path):
        """
            path: absolute path to repo

            return True if git repo exists
        """
        if os.path.isdir(path):
            g = os.path.join(path, '.git')
            if os.path.isdir(g):
                self.debug('initialzied repo {}'.format(path))
                self._repo = Repo(path)
                return True
            else:
                self.debug('{} is not a valid repo'.format(path))
                self._repo = Repo.init(path)

    def commit_dialog(self):

        from pychron.git_archive.commit_dialog import CommitDialog
        # print self.index.diff('HEAD')
        # print self._repo.head
        # hcommit = self._repo.head.commit
        # print hcommit.diff('HEAD~1')
        # print hcommit.diff(None)
        # ps = [diff.a_blob.name for diff in self._repo.head.commit.diff(None)]
        ps = self.get_local_changes()
        cd= CommitDialog(ps)
        info=cd.edit_traits()
        if info.result:
            index=self.index
            index.add([mp.path for mp in cd.valid_paths()])
            self.commit(cd.commit_message)
            return True

    def get_local_changes(self):
        repo = self._repo
        diff_str = repo.git.diff('HEAD', '--full-index')
        diff_str = StringIO(diff_str)
        diff_str.seek(0)
        diff = Diff._index_from_patch_format(repo, diff_str)
        return [di.a_blob.path for di in diff.iter_change_type('M')]

        # patches = map(str.strip, diff_str.split('diff --git'))
        # patches = ['\n'.join(p.split('\n')[2:]) for p in patches[1:]]
        #
        # diff_str = StringIO(diff_str)
        # diff_str.seek(0)
        # index = Diff._index_from_patch_format(repo, diff_str)
        #
        # return index, patches
        #
    def has_staged(self):
        return self._repo.is_dirty()

    def add_unstaged(self, root, extension=None, use_diff=False):
        index=self.index

        def func(ps, extension):
            if extension:
                if not isinstance(extension, tuple):
                    extension=(extension, )
                ps = [pp for pp in ps if os.path.splitext(pp)[1] in extension]

            if ps:
                self.debug('adding to index {}'.format(ps))
                index.add(ps)

        if use_diff:
            pass
            # try:
            #     ps = [diff.a_blob.path for diff in index.diff(None)]
            #     func(ps, extension)
            # except IOError,e:
            #     print e
        else:
            for r, ds, fs in os.walk(root):
                ps = [os.path.join(r,fi) for fi in fs]
                func(ps, extension)

    def update_gitignore(self, *args):
        p=os.path.join(self.path, '.gitignore')
        # mode = 'a' if os.path.isfile(p) else 'w'
        args=list(args)
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                for line in fileiter(fp, strip=True):
                    for i,ai in enumerate(args):
                        if line==ai:
                            args.pop(i)
        if args:
            with open(p,'a') as fp:
                for ai in args:
                    fp.write('{}\n'.format(ai))
            self._add_to_repo(p, msg='updated .gitignore')

    def get_commit(self, hexsha):
        repo=self._repo
        return repo.commit(hexsha)

    def tag_branch(self, tagname):
        repo = self._repo
        repo.create_tag(tagname)

    def get_current_branch(self):
        repo = self._repo
        return repo.active_branch.name

    def checkout_branch(self, name):
        repo=self._repo
        branch = getattr(repo.heads, name)
        branch.checkout()

        self.selected_branch=name
        self._load_branch_history()

    def create_branch(self, name):
        repo=self._repo
        if not name in repo.branches:
            branch = repo.create_head(name)
            branch.commit = repo.head.commit
            self.checkout_branch(name)

    def create_remote(self, url, name='origin'):
        repo=self._repo
        if repo:
            #only create remote if doesnt exist
            if not hasattr(repo.remotes, name):
                #     url='{}:jir812@{}:{}.git'.format(user, host, repo_name
                repo.create_remote(name, url)
                pass

    def pull(self, branch='master', remote='origin', handled=True):
        """
            fetch and merge
        """
        repo=self._repo
        remote = self._get_remote(remote)
        if remote:
            try:
                repo.git.pull(remote, branch)
            except GitCommandError, e:
                self.debug(e)
                if not handled:
                    raise e

    def push(self, branch='master', remote='origin'):
        repo=self._repo
        rr = self._get_remote(remote)
        if rr:
            repo.git.push(remote, branch)

    def merge(self, src, dest):
        repo = self._repo
        dest = getattr(repo.branches, dest)
        dest.checkout()

        src = getattr(repo.branches, src)
        repo.git.merge(src.commit)

    def commit(self, msg):
        index=self.index
        if index:
            index.commit(msg)

    def add(self, p, msg=None, msg_prefix=None, **kw):
        repo=self._repo
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
        self._add_to_repo(dest, msg, **kw)

    #private
    def _add_to_repo(self, p, msg, commit=True):
        index = self.index
        if index:
            if not isinstance(p, list):
                p=[p]

            index.add(p)
            if commit:
                index.commit(msg)

    def _get_remote(self, remote):
        repo=self._repo
        return getattr(repo.remotes, remote)

    def _load_branch_history(self):
        pass

    def _get_branch_history(self):
        repo=self._repo
        hexshas = repo.git.log('--pretty=%H').split('\n')
        return hexshas

    def _load_branch_history(self):
        hexshas = self._get_branch_history()
        self.commits = self._parse_commits(hexshas)

    def _parse_commits(self, hexshas):
        def factory(ci):
            repo = self._repo
            obj = repo.rev_parse(ci)
            cx = Commit(message=obj.message,
                        hexsha=obj.hexsha,
                        date=time.strftime("%m/%d/%Y %H:%M", time.gmtime(obj.committed_date)))
            return cx

        return [factory(ci) for ci in hexshas]

    def _load_file_history(self, p):
        repo = self._repo
        try:
            hexshas = repo.git.log('--pretty=%H', '--follow', '--', p).split('\n')
            # cs = [repo.rev_parse(c).message for c in hexshas]
            # self.selected_path_commits = cs
            self.selected_path_commits = self._parse_commits(hexshas)
        except GitCommandError:
            self.selected_path_commits = []

    #handlers
    def _selected_fired(self, new):
        if new:
            self._selected_hook(new)
            self._load_file_history(new)

    def _selected_hook(self, new):
        pass

    @property
    def index(self):
        return self._repo.index

if __name__ == '__main__':
    rp=GitRepoManager()
    rp.init_repo('/Users/ross/Pychrondata_dev/scripts')
    rp.commit_dialog()

#============= EOF =============================================
        #repo manager protocol
    # def get_local_changes(self, repo=None):
    #     repo = self._get_repo(repo)
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