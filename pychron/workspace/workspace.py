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
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.ui import set_qt

set_qt()
#============= enthought library imports =======================
from traitsui.handler import Controller
from traits.api import Instance, Button
from traitsui.api import View, Item
import yaml
#============= standard library imports ========================
import os
#============= local library imports  ==========================
import shutil
from git import Repo
from pychron.loggable import Loggable
from pychron.workspace.index import IndexAdapter, Base, AnalysisIndex

logging_setup('wm')


class WorkspaceManager(Loggable):
    _repo = None
    index_db = Instance(IndexAdapter)
    test = Button

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
            self.init_repo(p)
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
        im.add(repo=repo.working_dir, **kw)

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

    def schema_diff(self, attrs):
        """
            show the diff for the given schema keyword `attr` between the working and master
        """
        repo = self._repo
        master_commit = repo.heads.master.commit
        working_commit = repo.heads.working.commit

        ds = working_commit.diff(master_commit, create_patch=True)
        # ds = working_commit.diff(master_commit)

        if not isinstance(attrs, (tuple, list)):
            attrs = (attrs, )

        attr_diff = {}
        for ci in ds.iter_change_type('M'):
            a = ci.a_blob.data_stream

            ayd = yaml.load(a)
            # print 'a', a.read()
            b = ci.b_blob.data_stream

            byd = yaml.load(b)
            for attr in attrs:

                try:
                    av = ayd[attr]
                except KeyError:
                    av = None

                try:
                    bv = byd[attr]
                except KeyError:
                    bv = None

                attr_diff[attr] = av == bv, av, bv

        return attr_diff

    def _test_fired(self):
        print self.schema_diff('age')
        # self.schema_diff('error')


class TestController(Controller):
    def traits_view(self):
        v = View(Item('test'))
        return v


if __name__ == '__main__':
    root = os.path.expanduser('~')
    root = os.path.join(root, 'Sandbox', 'workspace')
    wm = WorkspaceManager()
    wm.create_repo('test', root, None)

    idx = IndexAdapter(path=os.path.join(root, 'index.db'),
                       schema=AnalysisIndex)
    idx.connect()

    idx.create_all(Base.metadata)

    wm.index_db = idx

    tpath = os.path.join(root, 'record.yaml')
    wm.add_record(tpath, identifier='12345', aliquot=1)

    tpath = os.path.join(root, 'record2.yaml')
    wm.add_record(tpath, identifier='12345', aliquot=2)

    mpath = os.path.join(root, 'test', 'record2.yaml')

    with open(mpath, 'w') as fp:
        d = dict(age=10, error=0.1)
        yaml.dump(d, fp, default_flow_style=False)

    wm.modify_record(mpath)

    tc = TestController(model=wm)
    tc.configure_traits()
    # print wm.schema_diff(('age', 'error'))
    # wm.commit_modification()
    # print wm.schema_diff(('age', 'error'))



#============= EOF =============================================



