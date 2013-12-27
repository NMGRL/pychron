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
        manager a local git repository

    """

    _repo=Any

    def add_repo(self, localpath):
        """
            add a blank repo at ``localpath``
        """
        repo=self._add_repo(localpath)
        self._repo=repo

    def set_remote(self, remotepath, remotename, name='origin', repo=None):
        repo=self._get_repo(repo)
        if repo:
            repo.create_remote(name, 'git@{}:{}.git'.format(remotepath,remotename))

    def update_local(self, repo=None):
        repo=self._get_repo(repo)
        if repo:
            repo.fetch()
            repo.pull()

    def publish_local(self, repo=None):
        repo=self._get_repo(repo)
        if repo:
            repo.push()

    def _add_to_repo(self, p, repo=None):

        repo=self._get_repo(repo)

        name = os.path.basename(p)
        index = repo.index
        index.add([name])
        index.commit('added {}'.format(p))

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
