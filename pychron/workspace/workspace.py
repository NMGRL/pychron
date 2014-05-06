#===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt
set_qt()
#============= enthought library imports =======================
from traits.api import Instance
#============= standard library imports ========================
import os
#============= local library imports  ==========================
import shutil
from git import Repo
from pychron.loggable import Loggable
from pychron.workspace.index import IndexAdapter, Base, AnalysisIndex


class WorkspaceManager(Loggable):
    _repo = None
    index_db = Instance(IndexAdapter)

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

        self.debug('{} is not a valid repo'.format(path))

    def create_repo(self, name, root, index):
        """
            name: name of repo
            root: root directory to create new repo
            index: path to sqlite index

            create master and working branches
        """

        p = os.path.join(root, name)
        if os.path.isdir(p):
            return

        os.mkdir(p)
        repo = Repo.init(p)
        self._repo = repo

    def add_record(self, path, commit=True, message=None, **kw):
        """
            path: absolute path to flat file
            commit: commit changes
            message: message to use for commit


            1. copy file at path to the repository
            2. add record to index

        """

        repo = self._repo

        #copy file to repo
        dest = os.path.join(repo.working_dir, os.path.basename(path))
        shutil.copyfile(path, dest)

        #add to master changeset
        index = repo.index
        index.add([dest])
        if commit:
            if message is None:
                message = 'added record {}'.format(path)
            index.commit(message)

            if 'working' in repo.branches:
                working = repo.heads.working
            else:
                working = repo.create_head('working')

            working.commit = repo.head.commit

        #add to sqlite index
        im = self.index_db
        im.add(repo=repo.working_dir,
               **kw)

    def modify_record(self, path, message=None):
        """
            commit the modification to path to the working branch
        """
        repo = self._repo

        repo.heads.working.checkout()

        index = repo.index
        index.add([path])

        if message is None:
            message = 'modified record {}'.format(path)
        index.commit(message)

    def commit_modification(self):
        """
            set the current working commit to the master head
        """
        repo = self._repo

        master = repo.heads.master
        master.commit = repo.head.commit
        master.checkout()


if __name__ == '__main__':
    root = os.path.expanduser('~')
    root = os.path.join(root, 'Sandbox','workspace')
    # root = '/Users/ross/Sandbox/workspace'
    wm = WorkspaceManager()
    idx = IndexAdapter(path=os.path.join(root, 'index.db'),
                       schema=AnalysisIndex)
    idx.connect()

    idx.create_all(Base.metadata)

    wm.index_db = idx
    wm.create_repo('test', root, None)

    tpath = os.path.join(root, 'record.txt')
    wm.add_record(tpath, identifier='12345', aliquot=1)

    tpath = os.path.join(root, 'record2.txt')
    wm.add_record(tpath, identifier='12345', aliquot=2)

    mpath = os.path.join(root, 'test', 'record2.txt')
    with open(mpath, 'w') as fp:
        fp.write('test modification')

    wm.modify_record(mpath)
    wm.commit_modification()



#============= EOF =============================================



