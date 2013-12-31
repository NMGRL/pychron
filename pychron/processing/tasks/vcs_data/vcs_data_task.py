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
import os
from pyface.tasks.action.schema import SToolBar
import apptools.sweet_pickle as pickle
from traits.api import List, Str, Instance, Any

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.processing.tasks.actions.vcs_actions import PushVCSAction, PullVCSAction, CommitVCSAction, ShareVCSAction
from pychron.processing.tasks.vcs_data.panes import VCSCentralPane
from pychron.processing.vcs_data.diff import Diff
from pychron.processing.vcs_data.vcs_manager import IsotopeVCSManager


class VCSDataTask(BaseManagerTask):
    id='pychron.processing.vcs'
    diffs=List
    selected_diff=Any

    tool_bars = [SToolBar(PushVCSAction(),
                          PullVCSAction(),
                          CommitVCSAction(),
                          ShareVCSAction())]

    selected_repository=Str
    repositories=List
    vcs=Instance(IsotopeVCSManager, ())

    commit_message=Str

    def prepare_destroy(self):
        if self.commit_message:
            if self._commit_messages:
                if not self._commit_messages[-1]==self.commit_message:
                    self._commit_messages.append(self.commit_message)

        p=os.path.join(paths.hidden_dir, 'commit_messages')
        with open(p, 'w') as fp:
            pickle.dump(self._commit_messages, fp)

    def activated(self):
        p = os.path.join(paths.hidden_dir, 'commit_messages')
        self._commit_messages=[]
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    ms=pickle.load(fp)
                    self._commit_messages=ms
                except pickle.PickleError:
                    pass

    def create_central_pane(self):
        return VCSCentralPane(model=self)

    def create_dock_panes(self):
        panes=[]
        return panes

    def initiate_push(self):
        pass

    def initiate_pull(self):
        pass

    def share(self):
        path = '/Users/ross/Sandbox/git/vcs_data.git'
        url = 'file://{}'.format(path)

        self.vcs.create_remote_repo(path)
        self.vcs.create_remote(url)

        self.vcs.push()

    def commit(self):
        #dont commit if there are no changes
        if self.diffs:
            if self.commit_message.strip():
                for di in self.diffs:
                    if di.use:
                        self.vcs.add(di.path, commit=False)

                self.vcs.commit_change(self.commit_message)
                self._commit_messages.append(self.commit_message)
            else:
                self.information_dialog('Please enter a comment for this commit')
        else:
            self.information_dialog('No changes to commit')

    def _selected_repository_changed(self):
        self.diffs = []
        self.selected_diff = Diff()

        self.vcs.set_repo(self.selected_repository)
        if self.vcs.is_dirty():
            self.diffs = self.vcs.get_diffs()

    def _repositories_default(self):
        root = paths.vcs_dir
        rs = [ri for ri in os.listdir(root)
              if os.path.isdir(os.path.join(root, ri, '.git'))]

        self.selected_repository = rs[0]
        return rs
#============= EOF ============================================= k

