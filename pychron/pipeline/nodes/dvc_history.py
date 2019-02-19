# ===============================================================================
# Copyright 2018 ross
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

from traits.api import HasTraits, List, Any, Str
from traitsui.api import UItem, TabularEditor, EnumEditor, VGroup

from pychron.core.helpers.iterfuncs import groupby_repo
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.git_archive.utils import get_commits
from pychron.git_archive.views import CommitAdapter
from pychron.pipeline.nodes.data import BaseDVCNode


class CommitSelector(HasTraits):
    commits = List
    selected = Any
    repo = Any
    branches = List
    branch = Str

    def load_branches(self):
        self.branches = self.repo.get_branch_names()
        b = self.repo.get_active_branch()
        self.branch = b

    def load_commits(self):
        cs = get_commits(self.repo.path, self.branch, None, '')
        self.commits = cs

    def traits_view(self):
        v = okcancel_view(VGroup(UItem('branch',
                                       editor=EnumEditor(name='branches')),
                                 UItem('commits',
                                       editor=TabularEditor(adapter=CommitAdapter(),
                                                            editable=False,
                                                            selected='selected'))),
                          height=600,
                          width=700)
        return v


class DVCHistoryNode(BaseDVCNode):
    options_klass = CommitSelector
    name = 'History Select'

    def pre_run(self, state, configure=True):
        unks = state.unknowns

        state.selected_commits = {}
        for repo, unks in groupby_repo(unks):
            # cs = get_commits(repo, , None, '')()
            cv = CommitSelector()
            repo = self.dvc.get_repository(repo)
            cv.repo = repo
            cv.load_branches()
            cv.load_commits()

            info = cv.edit_traits(kind='livemodal')
            if not info.result:
                return

            if not cv.selected:
                return
            state.selected_commits[repo.name] = cv.selected.hexsha
        return True

    def run(self, state):
        unks = state.unknowns

        for repo, ans in groupby_repo(unks):
            repo = self.dvc.get_repository(repo)
            abranch = repo.get_current_branch()
            branchname = 'history'
            repo.create_branch(branchname, state.selected_commits[repo.name], inform=False)

            pans = self.dvc.make_analyses(list(ans), reload=True)

            # only allow one history group for right now.
            # in the future add a history_group_id
            # analyses are then partitioned by group_id then history_group_id
            for unk in pans:
                unk.group_id = 1
                unk.history_id = 1

            branch = repo.get_branch(abranch)
            branch.checkout()
            repo.delete_branch(branchname)
            unks.extend(pans)

# ============= EOF =============================================
