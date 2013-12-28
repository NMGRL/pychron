#===============================================================================
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

from traits.api import Any

#============= standard library imports ========================
import os
from git import Repo
from git.utils import is_git_dir
#============= local library imports  ==========================
from pychron.loggable import Loggable


class RepoManager(Loggable):
    """
        manage a local git repository

    """

    _repo=Any

    def add_repo(self, localpath):
        """
            add a blank repo at ``localpath``
        """
        repo=self._add_repo(localpath)
        self._repo=repo

    def create_remote(self, host, repo_name, name='origin', repo=None, user='git'):
        repo=self._get_repo(repo)
        if repo:
            url='{}@{}:{}'.format(user, host, repo_name)
            repo.create_remote(name, url)

    #git protocol
    def update(self, repo=None, remote='origin'):
        remote=self._get_remote(repo, remote)
        if remote:
            remote.fetch()
            remote.pull()

    def push(self, repo=None, remote='origin'):
        remote = self._get_remote(repo, remote)
        if remote:
            remote.push()

    def commit(self, msg, repo):
        index=self._get_repo_index(repo)
        if index:
            index.commit(msg)

    def add(self, p, msg=None):
        if msg is None:
            msg='added {}'.format(p)

        self._add_to_repo(p, msg)

    def has_uncommitted(self, repo=None):
        return len(self._get_uncommited_changes(repo))

    #private
    def _get_uncommited_changes(self, repo):
        index=self._get_repo_index(repo)
        return index.diff(None)

    def _add_to_repo(self, p, msg, repo=None):
        # repo=self._get_repo(repo)
        # if repo:
        index=self._get_repo_index(repo)
        if index:
            name = os.path.basename(p)
            index.add([name])
            index.commit(msg)

    def _get_remote(self,repo, remote):
        repo=self._get_repo(repo)
        if repo:
            return getattr(repo.remotes, remote)

    def _get_repo_index(self, repo):
        repo=self._get_repo(repo)
        if repo:
            return repo.index

    def _get_repo(self, repo):
        if repo is None:
            repo = self._repo

        return repo

    def _add_repo(self, root):
        if not os.path.isdir(root):
            os.mkdir(root)

        gitdir=os.path.join(root, '.git')
        if not is_git_dir(gitdir):
            repo = Repo.init(root)
        else:
            repo = Repo(root)

        return repo

#============= EOF =============================================
